import pytest

from ecd.cli import main


def test_main(mocker, capsys):
    cmd = "ecd 2 2024 --part 1 --seed 3"
    mocker.patch("sys.argv", cmd.split())
    mock_get_inputs = mocker.patch("ecd.get_inputs", return_value={"1": "test data"})
    main()
    mock_get_inputs.assert_called_once_with(quest=2, event=2024, seed=3)
    out, err = capsys.readouterr()
    assert out.rstrip() == "test data"


def test_commutativity(mocker, capsys):
    cmd = "ecd 2024 1 --part 1"
    mocker.patch("sys.argv", cmd.split())
    mock_get_inputs = mocker.patch("ecd.get_inputs", return_value={"1": "test data"})
    main()
    mock_get_inputs.assert_called_once_with(quest=1, event=2024, seed=None)
    out, err = capsys.readouterr()
    assert out.rstrip() == "test data"


expected = """{
  "1": "data1",
  "2": "data2",
  "3": "data3"
}"""


def test_main_all_parts(mocker, capsys):
    cmd = "ecd 1 2024 --seed 2"
    mocker.patch("sys.argv", cmd.split())
    mock_get_inputs = mocker.patch("ecd.get_inputs")
    mock_get_inputs.return_value = {
        "1": "data1",
        "2": "data2",
        "3": "data3",
    }
    main()
    mock_get_inputs.assert_called_once_with(quest=1, event=2024, seed=2)
    out, err = capsys.readouterr()
    assert out.rstrip() == expected


def test_missing_part(mocker):
    cmd = "ecd 1 2024 --seed 2 --part 3"
    mocker.patch("sys.argv", cmd.split())
    mock_get_inputs = mocker.patch("ecd.get_inputs")
    mock_get_inputs.return_value = {
        "1": "data1",
        "2": "data2",
    }
    with pytest.raises(SystemExit("ERROR: part 3 is not available yet.")):
        main()
    mock_get_inputs.assert_called_once_with(quest=1, event=2024, seed=2)
