

class Transaction:
    """
    Representation of a transaction returned from the network.
    """

    def __init__(self, txid, block, amount_in, amount_out, amount_fee):
        self.txid = txid
        self.block = block

        if amount_in != amount_out + amount_fee:
            raise ArithmeticError("the amounts just don't add up!")

        self.amount_in = amount_in
        self.amount_out = amount_out
        self.amount_fee = amount_fee

        self.inputs = []
        self.outputs = []

    def add_input(self, part):
        self.inputs.append(part)

    def add_output(self, part):
        self.outputs.append(part)

    def __repr__(self):
        return "{} in block {} for {:.0f} satoshi ({:.0f} sent + {:.0f} fee) with {} input{} and {} output{}".format(
                self.txid, self.block, self.amount_in, self.amount_out, self.amount_fee,
                len(self.inputs), '' if len(self.inputs) == 1 else 's',
                len(self.outputs), '' if len(self.outputs) == 1 else 's')


class TxPart:
    """
    Representation of a single input or output.
    """

    def __init__(self, address, amount, asm=None):
        self.address = address
        self.amount = amount
        self.op_return = None

        if address is None and asm is not None:
            if asm.startswith('OP_RETURN '):
                self.op_return = asm[10:]
            elif asm.startswith('return ['):
                self.op_return = asm[8:-1]

    def message(self):
        """Attempt to decode the op_return value (if there is one) as a UTF-8 string."""

        if self.op_return is None:
            return None

        return bytearray.fromhex(self.op_return).decode('utf-8')

    def __repr__(self):
        if self.address is None and self.op_return is not None:
            return "OP_RETURN data with {:.0f} satoshi burned".format(self.amount)
        else:
            return "{} with {:.0f} satoshi".format(self.address, self.amount)

