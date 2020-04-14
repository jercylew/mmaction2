import os
import random
import tempfile

import numpy as np
import pytest
import torch
import torch.nn as nn
from mmcv import Config
from torch.utils.data import Dataset

from mmaction.core import set_random_seed, train_model
from mmaction.datasets.registry import DATASETS


@DATASETS.register_module
class ExampleDataset(Dataset):

    def __init__(self, test_mode=False):
        self.test_mode = test_mode

    def evaluate(self, results, logger=None):
        eval_results = dict()
        eval_results['test'] = 1
        return eval_results

    def __getitem__(self, idx):
        results = dict(imgs=torch.tensor([1]))
        return results

    def __len__(self):
        return 1


class ExampleModel(nn.Module):

    def __init__(self):
        super(ExampleModel, self).__init__()
        self.test_cfg = None
        self.conv1 = nn.Conv2d(3, 8, kernel_size=1)
        self.norm1 = nn.BatchNorm1d(2)

    def forward(self, imgs, return_loss=False):
        self.norm1(torch.rand(3, 2).cuda())
        losses = dict()
        losses['test_loss'] = torch.tensor([0.5], requires_grad=True)
        return losses


@pytest.mark.skipif(
    not torch.cuda.is_available(), reason='requires CUDA support')
def test_train_model():
    model = ExampleModel()
    dataset = ExampleDataset()
    cfg = dict(
        seed=0,
        gpus=1,
        resume_from=None,
        load_from=None,
        workflow=[('train', 1)],
        total_epochs=5,
        evaluation=dict(interval=1),
        data=dict(
            videos_per_gpu=1,
            workers_per_gpu=0,
            val=dict(type='ExampleDataset')),
        optimizer=dict(type='SGD', lr=0.01, momentum=0.9, weight_decay=0.0001),
        optimizer_config=dict(grad_clip=dict(max_norm=40, norm_type=2)),
        lr_config=dict(policy='step', step=[40, 80]),
        checkpoint_config=dict(interval=10),
        log_level='INFO',
        log_config=dict(interval=20, hooks=[dict(type='TextLoggerHook')]))

    # test _non_dist_train
    with tempfile.TemporaryDirectory() as tmpdir:
        # normal train
        cfg['work_dir'] = tmpdir
        config = Config(cfg)
        train_model(model, dataset, config)

    with tempfile.TemporaryDirectory() as tmpdir:
        # train with validation
        cfg['work_dir'] = tmpdir
        config = Config(cfg)
        train_model(model, dataset, config, validate=True)

    with tempfile.TemporaryDirectory() as tmpdir:
        # train with Fp16OptimizerHook
        cfg['work_dir'] = tmpdir
        cfg['fp16'] = dict(loss_scale=512.)
        config = Config(cfg)
        model.fp16_enabled = None
        train_model(model, dataset, config)


def test_set_random_seed():
    set_random_seed(0)
    a_random = random.randint(0, 10)
    a_np_random = np.random.rand(2, 2)
    a_torch_random = torch.rand(2, 2)
    if torch.__version__ != 'parrots':
        assert torch.backends.cudnn.deterministic is False
    assert torch.backends.cudnn.benchmark is False
    assert os.environ['PYTHONHASHSEED'] == str(0)

    set_random_seed(0, True)
    b_random = random.randint(0, 10)
    b_np_random = np.random.rand(2, 2)
    b_torch_random = torch.rand(2, 2)
    if torch.__version__ != 'parrots':
        assert torch.backends.cudnn.deterministic is True
    assert torch.backends.cudnn.benchmark is False

    assert a_random == b_random
    assert np.equal(a_np_random, b_np_random).all()
    assert torch.equal(a_torch_random, b_torch_random)