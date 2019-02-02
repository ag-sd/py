import yaml


class Executable:
    def __init__(self, executable, description):
        self.executable = executable
        self.description = description


class Plugin:
    def __init__(self, plugin_yaml):
        with open(plugin_yaml, 'r') as stream:
            try:
                plugin = yaml.load(stream)
                self.name = plugin["name"]
                self.description = plugin["description"]
                self.version = plugin["version"]
                self.author = plugin["author"]
                self.input_extensions = plugin["input_extensions"]
                self.configuration = Executable(
                    plugin["configuration"][0]["executable"],
                    plugin["configuration"][0]["description"])
                self.execution = []
                for execution_step in plugin["execution"]:
                    self.execution.append(Executable(
                        execution_step["executable"],
                        execution_step["description"]
                    ))
            except yaml.YAMLError:
                raise ValueError("An error occurred. This plugin cannot be loaded", yaml.YAMLError)
