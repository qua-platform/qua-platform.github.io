from qm.qua import *

with program() as input_stream_use:
    stream = declare_input_stream(int, "stream_a")
    advance_input_stream(stream)
