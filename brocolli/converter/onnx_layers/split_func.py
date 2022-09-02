from loguru import logger
from onnx import helper
from onnx import TensorProto as tp
import onnx_layers as ops
import numpy as np

from onnx_layers.base_layer import BaseLayer


class SplitFunc(BaseLayer):
    def __init__(self, source_node, module=None, auto_gen=True):
        super(SplitFunc, self).__init__(source_node, module, auto_gen)

    def get_split_attr(self):
        attr_dict = {"axis": 0}
        if "dim" in self._source_node.kwargs:
            dim = self._source_node.kwargs["dim"]
        else:
            dim = self.list_try_get(self._source_node.args, 2, 0)

        attr_dict["axis"] = dim

        return attr_dict

    def add_bottom_top(self, in_names=None, out_names=None):
        if in_names is None:
            in_names = [self.recursive_find_name(self._source_node.args[0])]

        if out_names is None:
            out_names = []
            for idx in range(len(self._source_node.meta["tensor_meta"])):
                out_names.append(self._name + "_" + str(idx))

        self._in_names.extend(in_names)
        self._out_names.extend(out_names)

    def generate_node(self, name=None, params=None, attr_dict=None):
        if params is None:
            if "dim" in self._source_node.kwargs:
                axis = self._source_node.kwargs["dim"]
            else:
                axis = self._source_node.args[2]

            shape = []
            for idx in range(len(self._source_node.meta["tensor_meta"])):
                tensor_meta = self._source_node.meta["tensor_meta"][idx]
                slice_shape = tensor_meta.shape[axis]
                shape.append(slice_shape)

            params = np.array(shape)

        if attr_dict is None:
            attr_dict = self.get_split_attr()

        self.create_params(self._name + "_split", params, tp.INT64)

        node = helper.make_node(
            "Split", self._in_names, self._out_names, self._name, **attr_dict
        )
        logger.info("split_layer: " + self._name + " created")
        self._node.append(node)