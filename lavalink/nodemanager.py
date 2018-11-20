import logging
from .node import Node

log = logging.getLogger('lavalink')


class NodeManager:
    def __init__(self, lavalink):
        self._lavalink = lavalink
        self.nodes = []

        self.regions = {
            'asia': ('hongkong', 'singapore', 'sydney', 'japan', 'southafrica'),
            'eu': ('eu', 'amsterdam', 'frankfurt', 'russia', 'vip-amsterdam', 'london'),
            'us': ('us', 'brazil', 'vip-us')
        }

    def add_node(self, host: str, port: int, password: str, region: str, name: str = None):
        """
        Adds a node
        ----------
        TODO
        """
        node = Node(self, host, port, password, region, name)
        self.nodes.append(node)

    def remove_node(self, node: Node):
        """
        Removes a node.
        ----------
        :param node:
            The node to remove from the list
        """
        self.nodes.remove(node)

    def get_region(self, endpoint: str):
        """
        Returns a Lavalink.py-friendly region from a Discord voice server address
        ----------
        :param endpoint:
            The address of the Discord voice server
        """
        if not endpoint:
            return None

        for key in self.regions:
            nodes = [n for n in self.nodes if n.region == key]

            if not nodes or not any(n.available for n in nodes):
                continue

            if endpoint.startswith(self.regions[key]):
                return key

        return None

    def find_ideal_node(self, region: str = None):
        """
        Finds the best (least used) node in the given region, if applicable.
        ----------
        :param region:
            The region to find a node in.
        """
        nodes = None
        if region:
            nodes = [n for n in self.nodes if n.region == region and n.available]

        if not nodes:  # If there are no regional nodes available, or a region wasn't specified.
            nodes = [n for n in self.nodes if n.available]

        if not nodes:
            return None

        best_node = min(nodes, key=lambda node: node.penalty)
        return best_node

    async def _node_connect(self, node: Node):
        log.info('Successfully connected to node `{}`'.format(node.name))
        # TODO: Dispatch node connected event

    async def _node_disconnect(self, node: Node, shutdown: bool, code: int, reason: str):
        log.warning('Disconnected from node `{}` ({}): {}'.format(node.name, code, reason))
        # TODO: Dispatch node disconnected event

        if shutdown:
            return
            #  Generally if a node is shutdown then it's probably being cleaned up
            #  perhaps if the bot is shutting down, so we shouldn't try to allocate
            #  the node's players to another node.

        best_node = self.find_ideal_node(node.region)

        if not best_node:
            log.error('Unable to move players, no available nodes!')
            return

        for player in node.players:
            await player.change_node(best_node)
