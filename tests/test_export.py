"""
Tests intended to run on CI to ensure that models are being correctly serialized.
To run the tests, first install the requirements by typing in:

pip install -r requirements.txt

Afterwards, from the project's root, type in:

pytest tests --weights="yolov5s.pt"

Check out the pytest website for more information
"""
import os
import shutil
import stat
import subprocess
import sys
import typing as t
from pathlib import Path

import pytest
import torch

FILE = Path(__file__).resolve()
ROOT = FILE.parents[1]  # YOLOv5 root directory
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))  # add ROOT to PATH

from export import export_formats, run

# Fixtures
# ----------------------


@pytest.fixture(scope='session')
def weights(pytestconfig):
    return pytestconfig.getoption('weights')


@pytest.fixture(scope="session")
def my_setup(request):
    def cleanup():
        for _, export_format_argument, suffix, ___ in cpu_export_formats():
            output_path = weights.replace('.pt', suffix.lower())
            if export_format_argument == 'tflite':
                output_path = weights.replace('.tflite', f'-int8.tflite')
            elif export_format_argument == 'edgetpu':
                output_path = weights.replace('.tflite', f'-int8_edgetpu.tflite')
            shutil.rmtree(output_path, onerror=del_rw)
    request.addfinalizer(cleanup)


# Utils
# ---------------------

def del_rw(action, name, exc):
    os.chmod(name, stat.S_IWRITE)
    os.remove(name)


def gpu_export_formats():
    formats = export_formats()
    return formats[formats['GPU'] == True].values.tolist()


def cpu_export_formats() -> t.List:
    """
    Get list of models that can be exported without gpu.
    Note that some of these require special environments to serialize.
    """
    formats = export_formats()
    return formats[formats['Format'].isin(
        ('ONNX', 'OpenVINO', 'CoreML', 'TensorFlow SavedModel', 'TensorFlow GraphDef',
        'TensorFlow Lite', 'TensorFlow Edge TPU', 'TensorFlow.js',)
    )].values.tolist()


# Tests
# ----------------------

def test_model_exists(weights: str):
    """
    Raise an error if model in specified path does not exist
    Args:
        weights: The path to yolov5 weight
    """
    assert weights is not None, 'Please specify --weights when running pytest.'
    assert weights.endswith('.pt'), f'weights must end with ".pt". Passed in: {weights}'
    assert os.path.exists(weights), f'Weights could not be found in: "{weights}"'


@pytest.mark.parametrize('export_format_row', cpu_export_formats())
def test_export_cpu(weights, export_format_row: t.List):
    _, export_format_argument, suffix, ___ = export_format_row
    if export_format_argument in ('engine', 'coreml'):
        pytest.skip(f'Export format: "{export_format_argument}" requires special environment. Skipping.')

    # make img small for quick tests
    img_sz = (160, 160)

    # As of now, openvino requires numpy < 1.20.
    # numpy will be downgraded during openvino run
    # so we need to re-upgrade numpy
    if export_format_argument == 'openvino':
        subprocess.run('pip install numpy==1.19.5', shell=True)
    elif export_format_argument == 'tfjs':
        subprocess.run('pip install --upgrade numpy', shell=True)

    # create the model
    run(weights=weights, imgsz=img_sz, include=(export_format_argument,), int8=True)
    output_path = weights.replace('.pt', suffix.lower())
    
    if os.path.isdir(output_path):
        # For now, we do a simple check to see whether files are not empty
        directory = os.fsencode(output_path)
        file_count = 0
        for subdir, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(subdir, file)
                file_count += 1
                file_is_not_empty = os.stat(file_path).st_size > 0
                assert file_is_not_empty, f'File: "{file_path}" should not be empty.'
        # Serialized folder should contain at least one file
        assert file_count > 0, 'Folder is empty'
    else:
        if export_format_argument == 'tflite':
            output_path = weights.replace('.tflite', f'-int8.tflite')
        elif export_format_argument == 'edgetpu':
            output_path = weights.replace('.tflite', f'-int8_edgetpu.tflite')
        assert os.path.exists(output_path), f'Failed to serialize "{output_path}".'

    # TODO: we can add new tests to check mAP of the exported model on VOC dataset


@pytest.mark.skipif(not torch.cuda.is_available(), reason='Test requires cuda')
@pytest.mark.parametrize('export_format_row', gpu_export_formats())
def test_export_gpu(export_format_row: t.List):
    # TODO: Test when runner with GPU is available
    pass
