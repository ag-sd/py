import os
import re
from enum import Enum

from PyQt5.QtWidgets import QComboBox, QBoxLayout, QLabel, QHBoxLayout, QCheckBox, QVBoxLayout, QWidget

from FileWrangler.FileWranglerCore import ConfigKeys, RenameUIOperation

"""
    {del}/{0} in {1}/{del}
    Algorithm:

    oh/this/is/A very Long/File-name
    Pattern: {del}/is/{del} {1}/{del}-{0}
    Separator:` - `
    will return -> name - Long

    # Preprocessing
    Step 1: Extract and sort all unique placeholders that should be applied from the source_template
        Ex: {del}/is/{del} {1}/{del}-{0} -> {[0-9]+} -> [{0}, {1}]

    Step 2: Find all tokens in template and create a token list where the index in the list points to the position
            in the source_template
        Ex: {del}/is/{del} {1}/{del}-{0} -> [{del},{del},{1},{del},{0}]

    Step 3: Transform source_template into a group match template
        Ex: {del}/is/{del} {1}/{del}-{0} -> (.+)/is/(.+) (.+)/(.+)-(.+)

    Step 4: Convert the group match template to a template with named subgroups
        Ex: {del}/is/{del} {1}/{del}-{0} -> (.+)/is/(.+) (.+)/(.+)-(.+) ->
            (?P<__del__0>.+)/is/(?P<__del__1>.+) (?P<__1__2>.+)/(?P<__del__3>.+)-(?P<__0__4>.+)

    # File Processing
    Step 4: Apply transformed group match template to the input filename and capture matches as a dict
        Ex: oh/this/is/A very Long/File-name -> {
                '__del__0': 'oh/this',
                '__del__1': 'A very',
                '__1__2': 'Long',
                '__del__3': 'File',
                '__0__4': 'name'
            }

    Step 5: For each entry in the group_dict,
            if it starts with __del__, drop it
            else tranform __x__y -> {x}
            place it into a new dictonary
        Ex: {'__del__0': 'oh/this', '__del__1': 'A very', '__1__2': 'Long', '__del__3': 'File', '__0__4': 'name'} ->
            {
                {1} -> 'Long',
                {0} -> 'name'
            }

    Step 6a: If ChangeStrategy = use_template
            for each key in the matches_lookup
                replace all occurences in the template
            If there are still unfilled tokens after that, raise an exception
        Ex: {1} - FOR _ {0} -> Long - FOR _ name
        Ex: {1} - FOR _ {2} -> Exception!!

    Step 6b: If ChangeStrategy = use_splitter
            for each group in the unique placeholder
                create a new list with matches
            splitter.join list and return
        Ex: [{0}, {1}], - > {0}-{1}

"""

NAME = "Pattern Extractor"
DESCRIPTION = "Finds and extracts patterns in the filename. You can specify parts of the directory names " \
              "to extract as well"

KEY_SOURCE_TEMPLATE = "Source_Template"
KEY_TARGET_TEMPLATE = "Target_Template"
KEY_TARGET_SPLITTER = "Target_Splitter"
KEY_CHANGE_STRATEGY = "Change_Strategy"
KEY_SOURCE_MARKERS = "Source_Markers"
KEY_SOURCE_TOKENS = "Source_Tokens"
KEY_SOURCE_GROUPS = "Source_Groups"
KEY_CONFIG_DIR_EX = "Exclude_Directory"
KEY_CONFIG_EXT_EX = "Exclude_Extension"

_MARKER_BEG_ = "{"
_MARKER_END_ = "}"
_MARKER_DEL_ = f"{_MARKER_BEG_}del{_MARKER_END_}"

_RE_MARKER_MATCH = re.compile(f"{_MARKER_BEG_}[0-9]+{_MARKER_END_}")

_RE_TOKEN_MATCH = re.compile(f"{_MARKER_BEG_}[0-9]+{_MARKER_END_}|{_MARKER_BEG_}del{_MARKER_END_}")
_RE_TOKEN_GROUP = re.compile("(.+)")


class ChangeStrategy(Enum):
    use_template = "Template"
    use_splitter = "Splitter"


def create_context(src_template: str, tgt_template: str,
                   change_mode: ChangeStrategy, splitter: str,
                   dir_exclude: bool, ext_exclude: bool):
    # Step 1: Extract and sort all unique placeholders that should be applied from the source_template
    #     Ex: {del}/is/{del} {1}/{del}-{0} -> {[0-9]+} -> [{0}, {1}]
    uniq_src_markers = list(set(_RE_MARKER_MATCH.findall(src_template)))
    source_markers = sorted(uniq_src_markers,
                            key=lambda x: int(x.replace(_MARKER_BEG_, "").replace(_MARKER_END_, "")))

    # Step 2: Find all tokens in template and create a token list where the index in the list points to the position
    #         in the source_template
    #     Ex: {del}/is/{del} {1}/{del}-{0} -> [{del},{del},{1},{del},{0}]
    source_template_tokens = _RE_TOKEN_MATCH.findall(src_template)

    # Step 3: Transform source_template into a group match template
    #     Ex: {del}/is/{del} {1}/{del}-{0} -> (.+)/is/(.+) (.+)/(.+)-(.+)
    named_groups = _RE_TOKEN_MATCH.sub(_RE_TOKEN_GROUP.pattern, src_template)

    # Step 4: Convert the group match template to a template with named subgroups
    #     Ex: {del}/is/{del} {1}/{del}-{0} -> (.+)/is/(.+) (.+)/(.+)-(.+) ->
    #         (?P<__del__0>.+)/is/(?P<__del__1>.+) (?P<__1__2>.+)/(?P<__del__3>.+)-(?P<__0__4>.+)
    for i in range(len(source_template_tokens)):
        group_name = f"__{source_template_tokens[i]}__{i}"
        group_name = group_name.replace(_MARKER_BEG_, "").replace(_MARKER_END_, "")
        named_groups = named_groups.replace("(.", f"(?P<{group_name}>.", 1)

    return {
        KEY_SOURCE_TEMPLATE: src_template,
        KEY_SOURCE_MARKERS: source_markers,
        KEY_SOURCE_GROUPS: named_groups,
        KEY_CONFIG_DIR_EX: dir_exclude,
        KEY_CONFIG_EXT_EX: ext_exclude,

        KEY_CHANGE_STRATEGY: change_mode,

        KEY_TARGET_TEMPLATE: tgt_template,
        KEY_TARGET_SPLITTER: splitter
    }


def get_key(file: str, context: dict) -> str:
    if context[KEY_CONFIG_DIR_EX]:
        _, file = os.path.split(file)

    if context[KEY_CONFIG_EXT_EX]:
        file, _ = os.path.splitext(file)

    # Step 4: Apply transformed group match template to the input filename and capture matches as a dict
    #     Ex: oh/this/is/A very Long/File-name -> {
    #             '__del__0': 'oh/this',
    #             '__del__1': 'A very',
    #             '__1__2': 'Long',
    #             '__del__3': 'File',
    #             '__0__4': 'name'
    #         }
    matches = re.match(context[KEY_SOURCE_GROUPS], file)

    # Step 5: For each entry in the group_dict,
    #         if it starts with __del__, drop it
    #         else tranform __x__y -> {x}
    #         place it into a new dictonary
    #     Ex: {'__del__0': 'oh/this', '__del__1': 'A very', '__1__2': 'Long',
    #          '__del__3': 'File', '__0__4': 'name'} ->
    #         {
    #             {1} -> 'Long',
    #             {0} -> 'name'
    #         }
    if matches is None:
        raise KeyError(f"Insufficient matches found in file {file} "
                       f"to satisfy the pattern {context[KEY_SOURCE_TEMPLATE]}")

    replacements = {}
    for key in matches.groupdict():
        if key.startswith("__del__"):
            continue
        value = matches[key]
        new_key = key.replace("__", _MARKER_BEG_, 1).replace("__", _MARKER_END_, 1)
        new_key = f"{new_key.split(_MARKER_END_)[0]}{_MARKER_END_}"
        replacements[new_key] = value

    match context[KEY_CHANGE_STRATEGY]:
        case ChangeStrategy.use_template:
            # Step 6: If ChangeStrategy = use_template
            #         for each key in the matches_lookup
            #             replace all occurrences in the template
            #         If there are still unfilled tokens after that, raise an exception
            #     Ex: {1} - FOR _ {0} -> Long - FOR _ name
            #     Ex: {1} - FOR _ {2} -> Exception!!
            key_base = context[KEY_TARGET_TEMPLATE]
            for k in replacements:
                key_base = key_base.replace(k, replacements[k])

            # If there are still unfilled tokens after that, raise an exception
            unfilled_matches = _RE_MARKER_MATCH.findall(key_base)
            if len(unfilled_matches) > 0:
                raise ValueError(f"Unfilled matches {unfilled_matches} found in file {file}")
            # Otherwise, everything is good
        case ChangeStrategy.use_splitter:
            # Step 6: If ChangeStrategy = use_splitter
            #         for each group in the unique placeholder
            #             create a new list with matches
            #         splitter.join list and return
            #     Ex: [{0}, {1}], - > {0}-{1}
            compiled = []
            for group in context[KEY_SOURCE_MARKERS]:
                if group not in replacements:
                    raise ValueError(f"Missing group {group} in found matches")
                compiled.append(replacements.pop(group))
            key_base = context[KEY_TARGET_SPLITTER].join(compiled)
        case _:
            raise ValueError(f"Unsupported change strategy received {context[KEY_CHANGE_STRATEGY]}")

    return key_base


class PatternExtractingUIOperation(RenameUIOperation):

    def __init__(self):
        super().__init__(name=NAME, description=DESCRIPTION)
        self.key_template = self._get_editable_combo()
        self.key_token = self._get_editable_combo()
        self.replacement_option = QComboBox()
        self.replacement_option.addItems([e.value for e in ChangeStrategy])
        self.exclude_dir_path = QCheckBox("Exclude directory path in format lookup")
        self.exclude_ext_path = QCheckBox("Exclude extension in format lookup")
        self.exclude_ext_path.setChecked(True)

        self.key_template.editTextChanged.connect(self._emit_merge_event)
        self.key_token.editTextChanged.connect(self._emit_merge_event)
        self.replacement_option.currentIndexChanged.connect(self._emit_merge_event)
        self.exclude_dir_path.stateChanged.connect(self._emit_merge_event)
        self.exclude_ext_path.stateChanged.connect(self._emit_merge_event)

    def _get_layout(self) -> QBoxLayout:
        key_layout = QHBoxLayout()
        key_layout.addWidget(QLabel("Format"))
        key_layout.addWidget(self.key_template, stretch=2)
        key_layout.addWidget(self.replacement_option)
        key_layout.addWidget(self.key_token, stretch=1)

        top_layout = QHBoxLayout()
        top_layout.addWidget(self.exclude_dir_path)
        top_layout.addWidget(self.exclude_ext_path)
        top_layout.addWidget(QWidget(), stretch=1)

        base_layout = QVBoxLayout()
        base_layout.addLayout(top_layout)
        base_layout.addLayout(key_layout)

        return base_layout

    def _get_key(self, file, config) -> str:
        # context = config[ConfigKeys.context]
        return get_key(file, config[ConfigKeys.context])

    def is_ready(self) -> bool:
        return not self._none_or_empty(self.key_template.currentText()) and \
               not self._none_or_empty(self.key_token.currentText())

    def get_context(self) -> dict:
        source_template = self.key_template.currentText()
        target_template = self.key_token.currentText()
        change_strategy = self.ChangeStrategy(self.replacement_option.currentText())
        target_splitter = self.key_token.currentText()

        return create_context(src_template=source_template, tgt_template=target_template,
                              change_mode=change_strategy, splitter=target_splitter,
                              dir_exclude=self.exclude_dir_path.isChecked(),
                              ext_exclude=self.exclude_ext_path.isChecked())

    def save_state(self):
        self._save_combo_current_text(self.key_template)
        self._save_combo_current_text(self.key_token)

    def get_help(self):
        _help = f"<h2>{self.name}</h2><p>{self.description}</p><h3>Details</h3>"
        _help += f"<p>Specify parts of the file path that should be used in the resulting file name. Use the " \
                 f"{{del}} tag to ignore parts of the file name and use numbered markers like {{0}}, {{1}} " \
                 f"to extract parts of the file</p>" \
                 f"<p>If <b>{self.exclude_dir_path.text()}</b> is checked, the format is applied only to the file name " \
                 f"(including file extension).</p>" \
                 f"<p>If <b>{self.exclude_ext_path.text()}</b> is checked, the extension is not included in the the " \
                 f"format expression.</p>" \
                 f"<p>The destination file name can either be defined using the <em>Template</em> option. " \
                 f"Alternatively, you can use the <em>Splitter</em> option, where all the extracted parts " \
                 f"of the file are joing with the splitter provided</p>"
        _help += f"<h3>Examples</h3>" \
                 f"<p>File: oh/this/is/A very Long/File-name.html<br>" \
                 f"Pattern: {{del}}/is/{{del}} {{1}}/{{del}}-{{0}}<br>" \
                 f"Splitter:' - '<br>" \
                 f"will return -> name - Long.html<br><b>Note:</b> If extension is included, the result will be " \
                 f"name.html - Long.html</p>" \
                 f"<p>File: oh/this/is/A very Long/File-name.html<br>" \
                 f"Pattern: {{del}}/is/{{del}} {{1}}/{{del}}-{{0}}<br>" \
                 f"Template:File{0} - {1}<br>" \
                 f"will return -> Filename - Long.html<br>If extension is included, the result will be " \
                 f"Filename.html - Long.html</p>"
        _help += f"<h3>Notes</h3>" \
                 f"<ol>" \
                 f"<li>The algorithm is greedy, so it will try to maximize each match</li>" \
                 f"</ol>"
        return _help
