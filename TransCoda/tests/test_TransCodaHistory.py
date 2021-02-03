import datetime

from TransCoda.core import TransCodaHistory
from TransCoda.core.Encoda import EncoderStatus


def test__insert_history_item():
    TransCodaHistory.del_history("TEST_FILE")
    TransCodaHistory.set_history("TEST_FILE", "OUTPUT", datetime.datetime.now(), datetime.datetime.now(), 100, 200,
                                 EncoderStatus.ERROR, "FOO", "ENCODER")
    result1 = TransCodaHistory.get_history("TEST_FILE")
    assert result1 is not None
    assert len(result1) == 1


def test__insert_updated_history_item():
    TransCodaHistory.del_history("TEST_FILE")
    TransCodaHistory.set_history("TEST_FILE", "OUTPUT", datetime.datetime.now(), datetime.datetime.now(), 100, 200,
                                 EncoderStatus.ERROR, "FOO", "ENCODER")
    result1 = TransCodaHistory.get_history("TEST_FILE")
    assert len(result1) == 1
    # Insert it again
    TransCodaHistory.set_history("TEST_FILE", "OUTPUT", datetime.datetime.now(), datetime.datetime.now(), 100, 200,
                                 EncoderStatus.ERROR, "FOO", "ENCODER")
    result2 = TransCodaHistory.get_history("TEST_FILE")
    assert len(result2) == 2


def test__fetch_history_item_exists():
    time_val = datetime.datetime.now()
    TransCodaHistory.del_history("TEST_FILE")
    TransCodaHistory.set_history("TEST_FILE", "OUTPUT", time_val, time_val, 100, 200, EncoderStatus.ERROR, "FOO", "ENC")
    result = TransCodaHistory.get_history("TEST_FILE")
    assert len(result) == 1
    value = result[0]
    assert value[TransCodaHistory.TransCodaHistoryFields.output_file] == "OUTPUT"
    assert value[TransCodaHistory.TransCodaHistoryFields.start_time] == time_val.strftime("%Y.%m.%d")
    assert value[TransCodaHistory.TransCodaHistoryFields.end_time] == time_val.strftime("%Y.%m.%d")
    assert value[TransCodaHistory.TransCodaHistoryFields.status] == EncoderStatus.ERROR
    assert value[TransCodaHistory.TransCodaHistoryFields.message] == "FOO"
    assert value[TransCodaHistory.TransCodaHistoryFields.encoder] == "ENC"
    assert value[TransCodaHistory.TransCodaHistoryFields.input_size] == 100
    assert value[TransCodaHistory.TransCodaHistoryFields.output_size] == 200


def test__fetch_history_item_not_exists():
    value = TransCodaHistory.get_history("TEST_IMAGINARY_FILE")
    assert value is None
