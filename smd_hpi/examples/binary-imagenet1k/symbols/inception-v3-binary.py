"""
Inception V3, suitable for images with around 299 x 299

Reference:

Szegedy, Christian, et al. "Rethinking the Inception Architecture for Computer Vision." arXiv preprint arXiv:1512.00567 (2015).
"""
import mxnet as mx
BIT = 1

def Conv(data, num_filter, kernel=(1, 1), stride=(1, 1), pad=(0, 0), name=None, suffix=''):
    conv = mx.sym.Convolution(data=data, num_filter=num_filter, kernel=kernel, stride=stride, pad=pad, no_bias=True, name='%s%s_conv2d' %(name, suffix))
    bn = mx.sym.BatchNorm(data=conv, name='%s%s_batchnorm' %(name, suffix), fix_gamma=True)
    act = mx.sym.Activation(data=bn, act_type='relu', name='%s%s_relu' %(name, suffix))
    return act

def QConv(data, num_filter, kernel=(1, 1), stride=(1, 1), pad=(0, 0), name=None, suffix='', with_bn_out=False):
    bn = mx.sym.BatchNorm(data=data, name='%s%s_batchnorm' %(name, suffix), fix_gamma=True)
    act = mx.sym.QActivation(data=bn, act_type='relu', name='%s%s_relu' %(name, suffix), act_bit=BIT, backward_only=True) 
    conv = mx.sym.QConvolution_v1(data=act, num_filter=num_filter, kernel=kernel, stride=stride, pad=pad, no_bias=True, name='%s%s_conv2d' %(name, suffix), 
                              act_bit=BIT)
    if with_bn_out:
      bn2 = mx.sym.BatchNorm(data=conv, name='%s%s_batchnorm' %(name, suffix), fix_gamma=True)
      return bn2
    else:
      return conv


def Inception7A(data,
                num_1x1,
                num_3x3_red, num_3x3_1, num_3x3_2,
                num_5x5_red, num_5x5,
                pool, proj,
                name):
    tower_1x1 = QConv(data, num_1x1, name=('%s_conv' % name))
    tower_5x5 = QConv(data, num_5x5_red, name=('%s_tower' % name), suffix='_conv')
    tower_5x5 = QConv(tower_5x5, num_5x5, kernel=(5, 5), pad=(2, 2), name=('%s_tower' % name), suffix='_conv_1')
    tower_3x3 = QConv(data, num_3x3_red, name=('%s_tower_1' % name), suffix='_conv')
    tower_3x3 = QConv(tower_3x3, num_3x3_1, kernel=(3, 3), pad=(1, 1), name=('%s_tower_1' % name), suffix='_conv_1')
    tower_3x3 = QConv(tower_3x3, num_3x3_2, kernel=(3, 3), pad=(1, 1), name=('%s_tower_1' % name), suffix='_conv_2')
    pooling = mx.sym.Pooling(data=data, kernel=(3, 3), stride=(1, 1), pad=(1, 1), pool_type=pool, name=('%s_pool_%s_pool' % (pool, name)))
    cproj = QConv(pooling, proj, name=('%s_tower_2' %  name), suffix='_conv')
    concat = mx.sym.Concat(*[tower_1x1, tower_5x5, tower_3x3, cproj], name='ch_concat_%s_chconcat' % name)
    concat = mx.sym.BatchNorm(data=concat, name='%s%s_batchnorm' %(name), fix_gamma=True)
    return concat

# First Downsample
def Inception7B(data,
                num_3x3,
                num_d3x3_red, num_d3x3_1, num_d3x3_2,
                pool,
                name):
    tower_3x3 = QConv(data, num_3x3, kernel=(3, 3), pad=(0, 0), stride=(2, 2), name=('%s_conv' % name))
    tower_d3x3 = QConv(data, num_d3x3_red, name=('%s_tower' % name), suffix='_conv')
    tower_d3x3 = QConv(tower_d3x3, num_d3x3_1, kernel=(3, 3), pad=(1, 1), stride=(1, 1), name=('%s_tower' % name), suffix='_conv_1')
    tower_d3x3 = QConv(tower_d3x3, num_d3x3_2, kernel=(3, 3), pad=(0, 0), stride=(2, 2), name=('%s_tower' % name), suffix='_conv_2')
    pooling = mx.symbol.Pooling(data=data, kernel=(3, 3), stride=(2, 2), pad=(0,0), pool_type="max", name=('max_pool_%s_pool' % name))
    concat = mx.sym.Concat(*[tower_3x3, tower_d3x3, pooling], name='ch_concat_%s_chconcat' % name)
    concat = mx.sym.BatchNorm(data=concat, name='%s%s_batchnorm' %(name), fix_gamma=True)
    return concat

def Inception7C(data,
                num_1x1,
                num_d7_red, num_d7_1, num_d7_2,
                num_q7_red, num_q7_1, num_q7_2, num_q7_3, num_q7_4,
                pool, proj,
                name):
    tower_1x1 = QConv(data=data, num_filter=num_1x1, kernel=(1, 1), name=('%s_conv' % name))
    tower_d7 = QConv(data=data, num_filter=num_d7_red, name=('%s_tower' % name), suffix='_conv')
    tower_d7 = QConv(data=tower_d7, num_filter=num_d7_1, kernel=(1, 7), pad=(0, 3), name=('%s_tower' % name), suffix='_conv_1')
    tower_d7 = QConv(data=tower_d7, num_filter=num_d7_2, kernel=(7, 1), pad=(3, 0), name=('%s_tower' % name), suffix='_conv_2')
    tower_q7 = QConv(data=data, num_filter=num_q7_red, name=('%s_tower_1' % name), suffix='_conv')
    tower_q7 = QConv(data=tower_q7, num_filter=num_q7_1, kernel=(7, 1), pad=(3, 0), name=('%s_tower_1' % name), suffix='_conv_1')
    tower_q7 = QConv(data=tower_q7, num_filter=num_q7_2, kernel=(1, 7), pad=(0, 3), name=('%s_tower_1' % name), suffix='_conv_2')
    tower_q7 = QConv(data=tower_q7, num_filter=num_q7_3, kernel=(7, 1), pad=(3, 0), name=('%s_tower_1' % name), suffix='_conv_3')
    tower_q7 = QConv(data=tower_q7, num_filter=num_q7_4, kernel=(1, 7), pad=(0, 3), name=('%s_tower_1' % name), suffix='_conv_4')
    pooling = mx.sym.Pooling(data=data, kernel=(3, 3), stride=(1, 1), pad=(1, 1), pool_type=pool, name=('%s_pool_%s_pool' % (pool, name)))
    cproj = QConv(data=pooling, num_filter=proj, kernel=(1, 1), name=('%s_tower_2' %  name), suffix='_conv')
    # concat
    concat = mx.sym.Concat(*[tower_1x1, tower_d7, tower_q7, cproj], name='ch_concat_%s_chconcat' % name)
    concat = mx.sym.BatchNorm(data=concat, name='%s%s_batchnorm' %(name), fix_gamma=True)
    return concat

def Inception7D(data,
                num_3x3_red, num_3x3,
                num_d7_3x3_red, num_d7_1, num_d7_2, num_d7_3x3,
                pool,
                name):
    tower_3x3 = QConv(data=data, num_filter=num_3x3_red, name=('%s_tower' % name), suffix='_conv')
    tower_3x3 = QConv(data=tower_3x3, num_filter=num_3x3, kernel=(3, 3), pad=(0,0), stride=(2, 2), name=('%s_tower' % name), suffix='_conv_1')
    tower_d7_3x3 = QConv(data=data, num_filter=num_d7_3x3_red, name=('%s_tower_1' % name), suffix='_conv')
    tower_d7_3x3 = QConv(data=tower_d7_3x3, num_filter=num_d7_1, kernel=(1, 7), pad=(0, 3), name=('%s_tower_1' % name), suffix='_conv_1')
    tower_d7_3x3 = QConv(data=tower_d7_3x3, num_filter=num_d7_2, kernel=(7, 1), pad=(3, 0), name=('%s_tower_1' % name), suffix='_conv_2')
    tower_d7_3x3 = QConv(data=tower_d7_3x3, num_filter=num_d7_3x3, kernel=(3, 3), stride=(2, 2), name=('%s_tower_1' % name), suffix='_conv_3')
    pooling = mx.sym.Pooling(data=data, kernel=(3, 3), stride=(2, 2), pool_type=pool, name=('%s_pool_%s_pool' % (pool, name)))
    # concat
    concat = mx.sym.Concat(*[tower_3x3, tower_d7_3x3, pooling], name='ch_concat_%s_chconcat' % name)
    concat = mx.sym.BatchNorm(data=concat, name='%s%s_batchnorm' %(name), fix_gamma=True)
    return concat

def Inception7E(data,
                num_1x1,
                num_d3_red, num_d3_1, num_d3_2,
                num_3x3_d3_red, num_3x3, num_3x3_d3_1, num_3x3_d3_2,
                pool, proj,
                name):
    tower_1x1 = QConv(data=data, num_filter=num_1x1, kernel=(1, 1), name=('%s_conv' % name))
    tower_d3 = QConv(data=data, num_filter=num_d3_red, name=('%s_tower' % name), suffix='_conv')
    tower_d3_a = QConv(data=tower_d3, num_filter=num_d3_1, kernel=(1, 3), pad=(0, 1), name=('%s_tower' % name), suffix='_mixed_conv')
    tower_d3_b = QConv(data=tower_d3, num_filter=num_d3_2, kernel=(3, 1), pad=(1, 0), name=('%s_tower' % name), suffix='_mixed_conv_1')
    tower_3x3_d3 = QConv(data=data, num_filter=num_3x3_d3_red, name=('%s_tower_1' % name), suffix='_conv')
    tower_3x3_d3 = QConv(data=tower_3x3_d3, num_filter=num_3x3, kernel=(3, 3), pad=(1, 1), name=('%s_tower_1' % name), suffix='_conv_1')
    tower_3x3_d3_a = QConv(data=tower_3x3_d3, num_filter=num_3x3_d3_1, kernel=(1, 3), pad=(0, 1), name=('%s_tower_1' % name), suffix='_mixed_conv')
    tower_3x3_d3_b = QConv(data=tower_3x3_d3, num_filter=num_3x3_d3_2, kernel=(3, 1), pad=(1, 0), name=('%s_tower_1' % name), suffix='_mixed_conv_1')
    pooling = mx.sym.Pooling(data=data, kernel=(3, 3), stride=(1, 1), pad=(1, 1), pool_type=pool, name=('%s_pool_%s_pool' % (pool, name)))
    cproj = QConv(data=pooling, num_filter=proj, kernel=(1, 1), name=('%s_tower_2' %  name), suffix='_conv')
    # concat
    concat = mx.sym.Concat(*[tower_1x1, tower_d3_a, tower_d3_b, tower_3x3_d3_a, tower_3x3_d3_b, cproj], name='ch_concat_%s_chconcat' % name)
    concat = mx.sym.BatchNorm(data=concat, name='%s%s_batchnorm' %(name), fix_gamma=True)
    return concat

# In[49]:

def get_symbol(num_classes=1000, **kwargs):
    data = mx.symbol.Variable(name="data")
    # stage 1
    conv = Conv(data, 32, kernel=(3, 3), stride=(2, 2), name="conv")
    conv_1 = QConv(conv, 32, kernel=(3, 3), name="conv_1")
    conv_2 = QConv(conv_1, 64, kernel=(3, 3), pad=(1, 1), name="conv_2", with_bn_out=True)
    pool = mx.sym.Pooling(data=conv_2, kernel=(3, 3), stride=(2, 2), pool_type="max", name="pool")
    # stage 2
    conv_3 = QConv(pool, 80, kernel=(1, 1), name="conv_3")
    conv_4 = QConv(conv_3, 192, kernel=(3, 3), name="conv_4", with_bn_out=True)
    pool1 = mx.sym.Pooling(data=conv_4, kernel=(3, 3), stride=(2, 2), pool_type="max", name="pool1")
    # stage 3
    in3a = Inception7A(pool1, 64,
                       64, 96, 96,
                       48, 64,
                       "avg", 32, "mixed")
    in3b = Inception7A(in3a, 64,
                       64, 96, 96,
                       48, 64,
                       "avg", 64, "mixed_1")
    in3c = Inception7A(in3b, 64,
                       64, 96, 96,
                       48, 64,
                       "avg", 64, "mixed_2")
    in3d = Inception7B(in3c, 384,
                       64, 96, 96,
                       "max", "mixed_3")
    # stage 4
    in4a = Inception7C(in3d, 192,
                       128, 128, 192,
                       128, 128, 128, 128, 192,
                       "avg", 192, "mixed_4")
    in4b = Inception7C(in4a, 192,
                       160, 160, 192,
                       160, 160, 160, 160, 192,
                       "avg", 192, "mixed_5")
    in4c = Inception7C(in4b, 192,
                       160, 160, 192,
                       160, 160, 160, 160, 192,
                       "avg", 192, "mixed_6")
    in4d = Inception7C(in4c, 192,
                       192, 192, 192,
                       192, 192, 192, 192, 192,
                       "avg", 192, "mixed_7")
    in4e = Inception7D(in4d, 192, 320,
                       192, 192, 192, 192,
                       "max", "mixed_8")
    # stage 5
    in5a = Inception7E(in4e, 320,
                       384, 384, 384,
                       448, 384, 384, 384,
                       "avg", 192, "mixed_9")
    in5b = Inception7E(in5a, 320,
                       384, 384, 384,
                       448, 384, 384, 384,
                       "max", 192, "mixed_10")
    # pool
    pool = mx.sym.Pooling(data=in5b, kernel=(8, 8), stride=(1, 1), pool_type="avg", name="global_pool")
    flatten = mx.sym.Flatten(data=pool, name="flatten")
    fc1 = mx.symbol.FullyConnected(data=flatten, num_hidden=num_classes, name='fc1')
    softmax = mx.symbol.SoftmaxOutput(data=fc1, name='softmax')
    return softmax
