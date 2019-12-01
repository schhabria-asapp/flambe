import torch
import torch.nn as nn
from torch import Tensor

from flambe.nn.mlp import MLPEncoder
from flambe.nn.module import Encoder


class MixtureOfSoftmax(Encoder):
    """Implement the MixtureOfSoftmax output layer.

    Attributes
    ----------
    pi: FullyConnected
        softmax layer over the different softmax
    layers: [FullyConnected]
        list of the k softmax layers

    """
    def __init__(self,
                 input_size: int,
                 output_size: int,
                 k: int = 1,
                 use_activation: bool = True,
                 take_log: bool = True) -> None:
        """Initialize the MOS layer.

        Parameters
        ----------
        input_size: int
            input dimension
        output_size: int
            output dimension
        k: int (Default: 1)
            number of softmax in the mixture

        """
        super().__init__()

        self.input_size = input_size
        self.output_size = output_size

        self.pi_w = MLPEncoder(input_size, k)
        self.softmax = nn.Softmax()

        self.layers = [MLPEncoder(input_size, output_size) for _ in range(k)]
        self.tanh = nn.Tanh()

        if use_activation:
            self.activation = nn.LogSoftmax() if take_log else nn.Softmax()

    @property
    def input_dim(self) -> int:
        """Get the size of the last dimension of an input.

        Returns
        -------
        int
            The size of the last dimension of an input.

        """
        return self.input_size

    @property
    def output_dim(self) -> int:
        """Get the size of the last dimension of an output.

        Returns
        -------
        int
            The size of the last dimension of an output.

        """
        return self.output_size

    def forward(self, data: Tensor) -> Tensor:  # type: ignore
        """Implement mixture of softmax for language modeling.

        Parameters
        ----------
        data: torch.Tensor
            seq_len x batch_size x hidden_size

        Return
        -------
        out: Variable
            output matrix of shape seq_len x batch_size x out_size

        """
        w = self.softmax(self.pi_w(data))
        # Compute k softmax, and combine using above weights
        out = [w[:, :, i] * self.tanh(W(data)) for i, W in enumerate(self.layers)]
        out = torch.cat(out, dim=0).sum(dim=0)
        if self.use_activation:
            out = self.activation(out)

        return out
