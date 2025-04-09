'''
Author: 孙石泉 786721684@qq.com
Date: 2024-02-27 08:26:13
LastEditTime: 2024-05-24 08:48:12
LastEditors: 孙石泉
Description: 
FilePath: \SD-UANET_load_balance-24-4-19\controller\ryu_operation\network_overload_node.py
'''

from ryu.base import app_manager  
from ryu.lib import hub
from ryu.base.app_manager import lookup_service_brick
from ryu.lib import hub
from ryu.ofproto import ofproto_v1_3


import numpy as np
from config import setting

class NetworkOverloadNode(app_manager.RyuApp):
    '''
    description: 获取网络的过载节点
    return {*}
    '''
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    def __init__(self, *args, **kwargs):
        super(NetworkOverloadNode, self).__init__(*args, **kwargs)
        self.name = 'overload_node'
        self.host_get_msg = lookup_service_brick("host_get_msg")
        self.structure = lookup_service_brick("structure")  # 创建一个Networkstructure的实例
        self.monitor = lookup_service_brick("monitor")  # 创建一个Networkmonitor的实例
        self.delay = lookup_service_brick("delay")  # 创建一个Networkdelay的实例

        
        self.find_overload_node_thread = hub.spawn(self.find_overload_node)
        # 重负载节点初始化为0
        self.overloaded_node = 0
    


    def calculate_network_status(self, Graph):
        '''
        description: 计算节点的网络状态属性的得分
        param {*} self
        param {*} graph
        return {*}
        '''
        # 网络拓扑中还没有获取到相关属性、第1次建立拓扑时不计算过载节点
        if self.monitor.port_remained_bw == {} or self.monitor.link_loss == {} or self.delay.link_delay == {} \
            or self.structure.first_flag == True:
            print("<overload_node.py> ---> Graph has not yet been enastablished")
            return None

        # 定义一个字典来存储每个节点的网络状态属性值
        network_status = {}
        graph = Graph

        # 获取链路最大及最小的带宽、时延和丢包率
        max_bandwidth = max([edge_attr.get('bw', 30000000) for u, v, edge_attr in graph.edges(data=True)])
        if max_bandwidth == 0.0:
            max_bandwidth = 30000000
        print("<overload_node.py> ---> max_bandwidth is:", max_bandwidth)
        max_delay = max([edge_attr.get('delay', 1) for u, v, edge_attr in graph.edges(data=True)])
        if max_delay == 0.01:
            max_delay = 0.02
        print("<overload_node.py> ---> max_delay is:", max_delay)
        max_loss = max([edge_attr.get('loss', 50) for u, v, edge_attr in graph.edges(data=True)])
        if max_loss == 0.0:
            max_delay = 5
        print("<overload_node.py> ---> max_loss is:", max_loss)

        min_bandwidth = min([edge_attr.get('bw', 0) for u, v, edge_attr in graph.edges(data=True)])
        print("<overload_node.py> ---> min_bandwidth is:", min_bandwidth)
        min_delay = min([edge_attr.get('delay', 0) for u, v, edge_attr in graph.edges(data=True)])
        print("<overload_node.py> ---> min_delay is:", min_delay)
        min_loss = min([edge_attr.get('loss', 0) for u, v, edge_attr in graph.edges(data=True)])
        print("<overload_node.py> ---> min_loss is:", min_loss)

        if max_bandwidth != min_bandwidth and max_delay != min_delay and max_loss != min_loss:

            # 计算每个节点的网络状态属性得分
            for node in graph.nodes:
                # 初始化网络状态属性得分
                node_status = 0
                # 获取节点的邻居列表
                neighbors = list(graph.neighbors(node))
                # 计算每个节点的网络状态属性得分
                for neighbor in neighbors:
                    # 获取连接属性
                    edge_attr = graph[node][neighbor]
                    # 假设剩余带宽、时延、丢包率越高越好，需要进行归一化处理。默认值取差一点，因为取默认值说明链路有问题
                    bandwidth = edge_attr.get('bw', 1000000)
                    delay = edge_attr.get('delay', 1)
                    loss = edge_attr.get('loss', 50)
                    # 归一化处理
                    bandwidth_norm = (bandwidth - min_bandwidth) / (max_bandwidth - min_bandwidth)
                    delay_norm = (delay- min_delay) / (max_delay - min_delay)
                    loss_norm = (loss - min_loss) / (max_loss - min_loss)
                    # 将链路属性值加权求和,分数越大越好（每项分值范围分别为 70 20 10）
                    link_score = setting.link_score_bandwidth_weight * bandwidth_norm * 100 \
                                 - setting.link_score_delay_weight * delay_norm * 100 \
                                 - setting.link_score_loss_weight * loss_norm * 100 \
                                 - 10
                    # 累加到节点的状态值
                    node_status += link_score
                
                # 存储节点的网络状态属性值（平均值）
                network_status[node] = (node_status) / (len(neighbors))
        
        return network_status



    def calculate_decision_scores(self, attribute_matrix):
        '''
        description: 计算多属性决策算法的得分
        param {*} attribute_matrix 属性矩阵（已模一化）
        return {*}
        '''
        # 计算理想解和负理想解(结果为一维数组，存储每个属性的正负理想解)
        ideal_solution = np.max(attribute_matrix, axis=0)
        negative_ideal_solution = np.min(attribute_matrix, axis=0)

        # 计算每个节点的综合得分
        scores = np.zeros(attribute_matrix.shape[0])
        for i in range(attribute_matrix.shape[0]):
            node_attributes = attribute_matrix[i]
            # 使用欧几里得距离计算节点与理想解的距离
            distance_to_ideal = np.linalg.norm(node_attributes - ideal_solution)
            distance_to_negative_ideal = np.linalg.norm(node_attributes - negative_ideal_solution)
            # 与正理想解的相对接近度,越大越好
            scores[i] = distance_to_negative_ideal / (distance_to_ideal + distance_to_negative_ideal)

        return scores





    def find_overload_node(self):
        '''
        description: 寻找网络中的过载节点(性能最差的节点)，ryu的子线程
        param {*} self
        return {*}
        '''
        hub.sleep(30)
        while True:

            # 网络拓扑中还没有获取到相关属性、第1次建立拓扑时不计算过载节点
            if self.monitor.port_remained_bw == {} or self.monitor.link_loss == {} or self.delay.link_delay == {} \
                or self.structure.first_flag == True:
                print("<overload_node.py> ---> Graph has not yet been enastablished")
                hub.sleep(5)
                continue

            self.graph = self.structure.network_topology

            
            # 每个节点的CPU占用率和内存占用率
            cpu_usage = {}
            memory_usage = {}
            for each_dpid in self.graph.nodes:
                if self.host_get_msg.all_switch_stats.get(each_dpid) != None:
                    cpu_usage[each_dpid] = self.host_get_msg.all_switch_stats[each_dpid][0]
                    memory_usage[each_dpid] = self.host_get_msg.all_switch_stats[each_dpid][1]
                else:
                    cpu_usage[each_dpid] = np.random.rand()
                    memory_usage[each_dpid] = np.random.rand()

            # 计算节点的网络状态属性值
            network_status = self.calculate_network_status(self.graph)

            print("<overload_node.py> ---> len(network_status) is:", len(network_status))
            print("<overload_node.py> ---> len(self.graph.nodes) is:", len(self.graph.nodes))
            if len(network_status) == len(self.graph.nodes):
                # 构建属性矩阵
                attribute_matrix = np.zeros((len(self.graph.nodes), 3))
                print("<overload_node.py>  节点列表：{}".format(self.graph.nodes))
                
                for i, node in enumerate(self.graph.nodes):
                    # 填充网络状态属性值、CPU占用率和内存使用率
                    attribute_matrix[i, 0] = network_status[node]
                    attribute_matrix[i, 1] = 1 / cpu_usage[node] + 1e-5
                    attribute_matrix[i, 2] = 1 / memory_usage[node] + 1e-5
                # 对属性矩阵进行模一化和加权
                for j in range(attribute_matrix.shape[1]):
                    col_values = attribute_matrix[:, j]
                    norm_factor = np.sqrt(np.sum(col_values ** 2))
                    if norm_factor != 0:
                        attribute_matrix[:, j] /= norm_factor
                    # 属性矩阵剩余对应的权重
                    attribute_matrix[:, j] *= setting.attribute_matrix_weight[j]
                # 计算多属性决策的得分,得分越大，节点性能越好
                decision_scores = self.calculate_decision_scores(attribute_matrix)
                print("<overload_node.py> ---> the result of MADA is:", decision_scores)
                # 找到过载节点（得分最小的节点）
                overloaded_node_index = np.argmin(decision_scores)
                self.overloaded_node = list(self.graph.nodes)[overloaded_node_index]
                print("<overload_node.py> ---> overloaded node is:", self.overloaded_node)
            
            hub.sleep(10)



        
