import json
import os
import sqlite3
from enum import Enum

from TransCoda.core.Encoda import EncoderStatus


class TransCodaHistoryFields(Enum):
    start_time = "start_time"
    end_time = "end_time"
    output_file = "output_file"
    status = "status"
    message = "message"
    output_size = "output_size"
    input_size = "input_size"
    encoder = "encoder"


_history_db = os.path.join(os.path.dirname(__file__), "../resource/history.json1.sqlite")

with sqlite3.connect(_history_db) as _db:
    _db.execute("CREATE TABLE IF NOT EXISTS history(file_name TEXT PRIMARY KEY, data json)")
    _db.commit()


def get_history(file_name):
    with sqlite3.connect(_history_db) as db:
        record = db.execute("SELECT data FROM history WHERE file_name=?", [file_name]).fetchone()

    if record is None:
        return None
    else:
        result = []
        json_array = json.loads(record[0])
        for execution in json_array:
            ex_item = {}
            for entry in execution:
                key = TransCodaHistoryFields[entry]
                if key == TransCodaHistoryFields.status:
                    value = EncoderStatus[execution[entry]]
                else:
                    value = execution[entry]
                ex_item[key] = value
            result.append(ex_item)
        return result


def set_history(input_file, output_file, start_time, end_time, input_size, output_size, status, message, encoder):
    data = [
        {
            TransCodaHistoryFields.output_file.name: output_file,
            TransCodaHistoryFields.start_time.value: start_time.strftime("%Y.%m.%d"),
            TransCodaHistoryFields.end_time.value: end_time.strftime("%Y.%m.%d"),
            TransCodaHistoryFields.status.value: status.name,
            TransCodaHistoryFields.message.value: message,
            TransCodaHistoryFields.input_size.value: input_size,
            TransCodaHistoryFields.output_size.value: output_size,
            TransCodaHistoryFields.encoder.value: encoder
        }
    ]

    with sqlite3.connect(_history_db) as db:
        db.execute("INSERT INTO history VALUES(?, ?)"
                   "ON CONFLICT (file_name) DO UPDATE SET "
                   "data=json_insert(data, '$[#]', json_extract(excluded.data, '$[0]'))", [input_file, json.dumps(data)])
        db.commit()


def del_history(file_name):
    with sqlite3.connect(_history_db) as db:
        db.execute("DELETE FROM history where file_name=?", [file_name])
        db.commit()