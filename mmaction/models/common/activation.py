import torch.nn as nn

activation_cfg = {
    # layer_abbreviation: module
    'ReLU': nn.ReLU,
    'LeakyReLU': nn.LeakyReLU,
    'PReLU': nn.PReLU,
    'RReLU': nn.RReLU,
    'ReLU6': nn.ReLU6,
    # TODO: add support for SELU and CELU
    # 'SELU': nn.SELU,
    # 'CELU': nn.CELU
}


def build_activation_layer(cfg):
    """ Build activation layer
    Args:
        cfg (dict): cfg should contain:
            type (str): Identify activation layer type.
            layer args: Args needed to instantiate a activation layer.
    Returns:
        layer (nn.Module): Created activation layer
    """
    if not (isinstance(cfg, dict) and 'type' in cfg):
        raise TypeError('cfg must be a dict containing the key "type"')
    cfg_ = cfg.copy()

    layer_type = cfg_.pop('type')
    if layer_type not in activation_cfg:
        raise KeyError('Unrecognized activation type {}'.format(layer_type))
    else:
        activation = activation_cfg[layer_type]
        if activation is None:
            raise NotImplementedError

    layer = activation(**cfg_)
    return layer