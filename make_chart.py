#!/usr/bin/python
"""
Create a graph from a file to show memory and CPU consumption
"""

import getopt
import sys
import plotly.plotly as py
import plotly.graph_objs as go

def usage():
    """
    print usage
    """
    print('non')

def main():
    """
    main function
    """

    try:
        opts, _ = getopt.getopt(sys.argv[1:], "hf:")
    except getopt.GetoptError as _:
        usage()
        sys.exit(2)

    for opt, arg in opts:
        if opt == "-h":
            usage()
            sys.exit()
        elif opt == "-f":
            graph = Graph()
            graph.make_graph(arg)
            graph.publish()
            sys.exit()
        else:
            assert False, "unhandled option"

class Graph(object):
    """
    Graph class with graph creation and publish
    """

    def __init__(self):
        self.time_x = []
        self.cpu_y = []
        self.memory_y = []
        self.load_y = []
        self.figure = None

    def make_graph(self, file_name):
        """
        create graph in dict format for plotly
        """
        graph_f = open(file_name, 'r')
        x_val = 0
        for index, line in enumerate(graph_f):
            if index % 4 == 0:
                # This is the time
                self.time_x.append(x_val)
                x_val += 30
            elif index % 4 == 1:
                # This is the CPU
                self.cpu_y.append(get_cpu(line))
            elif index % 4 == 2:
                # This is the memory
                self.memory_y.append(get_memory(line))
            elif index % 4 == 3:
                self.load_y.append(get_load(line))

        cpu_trace = get_trace(self.time_x, self.cpu_y, "CPU", "red")
        memory_trace = get_trace(self.time_x, self.memory_y, "MEMORY",
                                 "blue")
        load_trace = get_trace(self.time_x, self.load_y, "load average",
                               "grean")

        data = go.Data([cpu_trace, memory_trace, load_trace])
        layout = go.Layout(title="CPU, MEMORY consumption and load average",
                           xaxis={'title' : 'time (s)'},
                           yaxis={'title' : 'CPU and Memory load average'})
        self.figure = go.Figure(data=data, layout=layout)

    def publish(self):
        """
        public results on plot.ly
        """
        py.plot(self.figure, filename='Server consumption', auto_open=False)

def get_trace(x_axis, y_axis, name, color):
    """
    get the trace
    """
    return go.Scatter(x=x_axis, y=y_axis, line=dict(color=color),
                      mode="lines", name=name)

def get_cpu(line):
    """
    get the cpu
    """
    return 100.0 - float(line.split()[2].split('%')[0])

def get_load(line):
    """
    get the load average
    """
    return float(line.split(',')[0].split()[-1])

def get_memory(line):
    """
    get the memory
    """
    spl = line.split()
    return get_mem_value(spl)

def get_mem_value(mem):
    """
    get memory value
    """
    total = int(mem[1].split('G')[0])
    if mem[4][-1] == 'M':
        used = float(mem[4].split('M')[0]) / 1024.0
        swap_total = int(mem[7].split('G')[0])
        swap_used = int(mem[10].split('G')[0])
        total += swap_total - swap_used
    else:
        used = int(mem[4].split('G')[0])

    return total - used

if __name__ == "__main__":
    main()
