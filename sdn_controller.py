#!/usr/bin/env python3
# Basic SDN Controller Implementation
# SHA-256 Hash: a43f75ba5b044c25e1280cea21b6e43599f8638a0b8550436ea99ea02e5868ca

import hashlib
import time
import cmd
from collections import defaultdict

# Calculate SHA-256 hash of student ID + provided string
STUDENT_ID = "898927734"
HASH_TEXT = STUDENT_ID + "NeoDDaBRgX5a9"
WATERMARK = hashlib.sha256(HASH_TEXT.encode()).hexdigest()

class Flow:
    """Represents a network flow between two endpoints"""
    def __init__(self, src, dst, flow_id, priority=0, bandwidth=1):
        self.src = src
        self.dst = dst
        self.flow_id = flow_id
        self.priority = priority
        self.bandwidth = bandwidth
        self.path = []
        self.backup_path = []
        self.active = True
        
    def __str__(self):
        return f"Flow {self.flow_id}: {self.src} → {self.dst} (Priority: {self.priority}, BW: {self.bandwidth})"

class Link:
    """Represents a network link between two nodes"""
    def __init__(self, src, dst, capacity=10, weight=1, delay=1):
        self.src = src
        self.dst = dst
        self.capacity = capacity
        self.weight = weight
        self.delay = delay
        self.utilization = 0
        self.flows = set()
        
    def __str__(self):
        return f"Link {self.src} → {self.dst} (Util: {self.utilization}/{self.capacity})"
        
    def add_flow(self, flow):
        """Add a flow to this link and update utilization"""
        self.flows.add(flow.flow_id)
        self.utilization += flow.bandwidth
        
    def remove_flow(self, flow):
        """Remove a flow from this link and update utilization"""
        if flow.flow_id in self.flows:
            self.flows.remove(flow.flow_id)
            self.utilization -= flow.bandwidth

class SDNController:
    """
    Basic SDN Controller that manages a network topology, flows, and flow tables
    """
    def __init__(self):
        # Network nodes and edges
        self.nodes = set()
        self.links = {}  # (src, dst) -> Link object
        
        # Flow tracking
        self.flows = {}  # flow_id -> Flow object
        
        # Flow table for each switch (node)
        self.flow_tables = defaultdict(list)
        
        # Statistics
        self.stats = {
            'total_flows': 0,
            'active_flows': 0,
            'total_switches': 0,
            'total_links': 0
        }
        
        # Print banner with watermark
        print(f"SDN Controller Initialized")
        print(f"Watermark: {WATERMARK}")
        
    def add_node(self, node_id):
        """Add a switch/node to the network topology"""
        if node_id not in self.nodes:
            self.nodes.add(node_id)
            self.stats['total_switches'] += 1
            return True
        return False
            
    def remove_node(self, node_id):
        """Remove a switch/node from the network topology"""
        if node_id in self.nodes:
            # Remove all associated links
            links_to_remove = []
            for src, dst in self.links:
                if src == node_id or dst == node_id:
                    links_to_remove.append((src, dst))
            
            for link in links_to_remove:
                self.remove_link(link[0], link[1])
            
            # Remove the node
            self.nodes.remove(node_id)
            
            # Clean up flow tables
            if node_id in self.flow_tables:
                del self.flow_tables[node_id]
            
            self.stats['total_switches'] -= 1
            return True
        return False
            
    def add_link(self, src, dst, capacity=10, weight=1, delay=1, bidirectional=True):
        """Add a link between two switches"""
        # Ensure both nodes exist
        if src not in self.nodes or dst not in self.nodes:
            return False
            
        # Create link object
        link_key = (src, dst)
        self.links[link_key] = Link(src, dst, capacity, weight, delay)
        
        self.stats['total_links'] += 1
        
        # If bidirectional, add the reverse link as well
        if bidirectional and (dst, src) not in self.links:
            self.add_link(dst, src, capacity, weight, delay, False)
            
        return True
                
    def remove_link(self, src, dst):
        """Remove a link from the network"""
        link_key = (src, dst)
        if link_key in self.links:
            # Remove link object
            del self.links[link_key]
            
            self.stats['total_links'] -= 1
            return True
        return False
            
    def add_flow(self, src, dst, priority=0, bandwidth=1):
        """Add a new flow to the network"""
        # Check if src and dst exist
        if src not in self.nodes or dst not in self.nodes:
            return None
            
        # Generate flow ID
        flow_id = self.stats['total_flows'] + 1
        
        # Create flow object
        flow = Flow(src, dst, flow_id, priority, bandwidth)
        
        # Compute a simple path (direct link or through one hop)
        path = self._find_simple_path(src, dst)
        if not path:
            print(f"No path found for flow {flow_id}: {src} → {dst}")
            return None
            
        flow.path = path
        
        # Try to compute a backup path
        backup_path = self._find_backup_path(src, dst, path)
        if backup_path:
            flow.backup_path = backup_path
        
        # Install flow in the network
        self._install_flow(flow)
        
        # Add to flows dict
        self.flows[flow_id] = flow
        
        # Update stats
        self.stats['total_flows'] += 1
        self.stats['active_flows'] += 1
        
        return flow
    
    def _find_simple_path(self, src, dst):
        """Find a simple path between src and dst (direct or one hop)"""
        # Check direct link
        if (src, dst) in self.links:
            return [src, dst]
        
        # Try one-hop paths
        for node in self.nodes:
            if (src, node) in self.links and (node, dst) in self.links:
                return [src, node, dst]
        
        # If no path found, try to find any path
        return self._find_any_path(src, dst)
    
    def _find_any_path(self, src, dst):
        """Find any path between src and dst using simple BFS"""
        if src == dst:
            return [src]
            
        visited = set([src])
        queue = [(src, [src])]
        
        while queue:
            node, path = queue.pop(0)
            
            # Check all neighbors
            for neighbor in self._get_neighbors(node):
                if neighbor == dst:
                    return path + [neighbor]
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        
        return []
    
    def _get_neighbors(self, node):
        """Get all neighbors of a node"""
        neighbors = []
        for src, dst in self.links:
            if src == node:
                neighbors.append(dst)
        return neighbors
    
    def _find_backup_path(self, src, dst, primary_path):
        """Find a backup path that doesn't share links with the primary path"""
        if len(primary_path) < 2:
            return []
            
        # Create a set of links to avoid
        avoid_links = set()
        for i in range(len(primary_path) - 1):
            avoid_links.add((primary_path[i], primary_path[i+1]))
        
        # Find a path that avoids these links
        visited = set([src])
        queue = [(src, [src])]
        
        while queue:
            node, path = queue.pop(0)
            
            # Check all neighbors
            for neighbor in self._get_neighbors(node):
                # Skip if this link is in the primary path
                if (node, neighbor) in avoid_links:
                    continue
                    
                if neighbor == dst:
                    return path + [neighbor]
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        
        return []
    
    def _install_flow(self, flow):
        """Install flow in the network by updating link utilizations and flow tables"""
        if not flow.path:
            return False
            
        path = flow.path
        
        # Update link utilizations
        for i in range(len(path) - 1):
            src, dst = path[i], path[i+1]
            link_key = (src, dst)
            
            if link_key in self.links:
                self.links[link_key].add_flow(flow)
        
        # Install flow table entries
        for i in range(len(path) - 1):
            node = path[i]
            next_hop = path[i+1]
            
            # Create flow table entry
            entry = {
                'match': {
                    'src': flow.src,
                    'dst': flow.dst,
                    'flow_id': flow.flow_id
                },
                'action': {
                    'output': next_hop,
                    'priority': flow.priority
                },
                'stats': {
                    'packet_count': 0,
                    'byte_count': 0,
                    'last_match': time.time()
                }
            }
            
            self.flow_tables[node].append(entry)
            
            # Sort flow table by priority (highest first)
            self.flow_tables[node].sort(key=lambda x: x['action']['priority'], reverse=True)
        
        return True
    
    def remove_flow(self, flow_id):
        """Remove a flow from the network"""
        if flow_id in self.flows:
            flow = self.flows[flow_id]
            
            # Remove from links
            path = flow.path
            for i in range(len(path) - 1):
                src, dst = path[i], path[i+1]
                link_key = (src, dst)
                
                if link_key in self.links:
                    self.links[link_key].remove_flow(flow)
            
            # Remove from flow tables
            for node in self.flow_tables:
                self.flow_tables[node] = [entry for entry in self.flow_tables[node] 
                                         if entry['match']['flow_id'] != flow_id]
            
            # Remove from flows dict
            del self.flows[flow_id]
            
            # Update stats
            self.stats['active_flows'] -= 1
            
            return True
        return False
    
    def simulate_link_failure(self, src, dst):
        """Simulate a link failure between src and dst"""
        print(f"Simulating link failure: {src} → {dst}")
        
        # Find affected flows
        affected_flows = []
        link_key = (src, dst)
        
        if link_key in self.links:
            for flow_id in list(self.links[link_key].flows):
                if flow_id in self.flows:
                    affected_flows.append(self.flows[flow_id])
            
            # Remove the link
            self.remove_link(src, dst)
            
            # Reroute affected flows
            for flow in affected_flows:
                self._reroute_flow(flow)
            
            return True
        return False
    
    def _reroute_flow(self, flow):
        """Reroute a flow after a topology change"""
        # Remove flow from current path
        path = flow.path
        for i in range(len(path) - 1):
            src, dst = path[i], path[i+1]
            link_key = (src, dst)
            
            if link_key in self.links:
                self.links[link_key].remove_flow(flow)
        
        # Clear flow tables for this flow
        for node in self.flow_tables:
            self.flow_tables[node] = [entry for entry in self.flow_tables[node] 
                                     if entry['match']['flow_id'] != flow.flow_id]
        
        # If backup path exists, use it
        if flow.backup_path and self._validate_path(flow.backup_path):
            flow.path, flow.backup_path = flow.backup_path, []
            success = self._install_flow(flow)
            if success:
                print(f"Flow {flow.flow_id} rerouted using backup path")
                # Compute a new backup path
                flow.backup_path = self._find_backup_path(flow.src, flow.dst, flow.path)
                return True
        
        # Try to find a new path
        new_path = self._find_simple_path(flow.src, flow.dst)
        if new_path:
            flow.path = new_path
            flow.backup_path = self._find_backup_path(flow.src, flow.dst, new_path)
            success = self._install_flow(flow)
            if success:
                print(f"Flow {flow.flow_id} rerouted using new path")
                return True
        
        # If we couldn't reroute, mark the flow as inactive
        flow.active = False
        print(f"Flow {flow.flow_id} could not be rerouted - marked inactive")
        self.stats['active_flows'] -= 1
        return False
    
    def _validate_path(self, path):
        """Check if a path is still valid in the current topology"""
        if len(path) < 2:
            return False
            
        for i in range(len(path) - 1):
            if (path[i], path[i+1]) not in self.links:
                return False
        return True
    
    def print_flow_tables(self):
        """Print the flow tables for all switches"""
        for node, table in self.flow_tables.items():
            print(f"\nFlow Table for Switch {node}:")
            print("-" * 80)
            print(f"{'Match':<40} | {'Action':<20} | {'Stats'}")
            print("-" * 80)
            
            for entry in table:
                match_str = f"src={entry['match']['src']}, dst={entry['match']['dst']}, id={entry['match']['flow_id']}"
                action_str = f"output={entry['action']['output']}, pri={entry['action']['priority']}"
                stats_str = f"pkts={entry['stats']['packet_count']}, bytes={entry['stats']['byte_count']}"
                
                print(f"{match_str:<40} | {action_str:<20} | {stats_str}")
    
    def print_statistics(self):
        """Print controller statistics"""
        print("\nController Statistics:")
        print("-" * 40)
        for stat, value in self.stats.items():
            print(f"{stat.replace('_', ' ').title():<20}: {value}")
    
    def print_topology(self):
        """Print the current network topology"""
        print("\nNetwork Topology:")
        print("-" * 40)
        print(f"Nodes: {self.nodes}")
        print("\nLinks:")
        for (src, dst), link in self.links.items():
            print(f"  {src} → {dst} (Utilization: {link.utilization}/{link.capacity})")
    
    def print_flows(self):
        """Print all flows in the network"""
        print("\nActive Flows:")
        print("-" * 80)
        for flow_id, flow in self.flows.items():
            if flow.active:
                path_str = " → ".join(str(node) for node in flow.path)
                backup_str = " → ".join(str(node) for node in flow.backup_path) if flow.backup_path else "None"
                print(f"Flow {flow_id}: {flow.src} → {flow.dst} (Priority: {flow.priority}, BW: {flow.bandwidth})")
                print(f"  Primary Path: {path_str}")
                print(f"  Backup Path: {backup_str}")
        
        print("\nInactive Flows:")
        print("-" * 80)
        inactive_found = False
        for flow_id, flow in self.flows.items():
            if not flow.active:
                inactive_found = True
                print(f"Flow {flow_id}: {flow.src} → {flow.dst} (Priority: {flow.priority}, BW: {flow.bandwidth}) - INACTIVE")
        
        if not inactive_found:
            print("No inactive flows")

class SDNControllerCLI(cmd.Cmd):
    """Command-line interface for the SDN Controller"""
    intro = "SDN Controller CLI. Type help or ? to list commands.\n"
    prompt = "sdn> "
    
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        
    def do_add_node(self, arg):
        """Add a node to the network: add_node <node_id>"""
        try:
            node_id = arg.strip()
            if not node_id:
                print("Error: Node ID required")
                return
                
            success = self.controller.add_node(node_id)
            if success:
                print(f"Node {node_id} added successfully")
            else:
                print(f"Error: Node {node_id} already exists")
        except Exception as e:
            print(f"Error: {str(e)}")
    
    def do_add_link(self, arg):
        """Add a link between nodes: add_link <src> <dst> [capacity] [weight] [delay]"""
        try:
            args = arg.strip().split()
            if len(args) < 2:
                print("Error: Source and destination nodes required")
                return
                
            src, dst = args[0], args[1]
            capacity = int(args[2]) if len(args) > 2 else 10
            weight = int(args[3]) if len(args) > 3 else 1
            delay = int(args[4]) if len(args) > 4 else 1
            
            success = self.controller.add_link(src, dst, capacity, weight, delay)
            if success:
                print(f"Link {src} → {dst} added successfully")
            else:
                print(f"Error: Could not add link (nodes might not exist)")
        except Exception as e:
            print(f"Error: {str(e)}")
    
    def do_remove_node(self, arg):
        """Remove a node from the network: remove_node <node_id>"""
        try:
            node_id = arg.strip()
            if not node_id:
                print("Error: Node ID required")
                return
                
            success = self.controller.remove_node(node_id)
            if success:
                print(f"Node {node_id} removed successfully")
            else:
                print(f"Error: Node {node_id} not found")
        except Exception as e:
            print(f"Error: {str(e)}")
    
    def do_remove_link(self, arg):
        """Remove a link from the network: remove_link <src> <dst>"""
        try:
            args = arg.strip().split()
            if len(args) < 2:
                print("Error: Source and destination nodes required")
                return
                
            src, dst = args[0], args[1]
            success = self.controller.remove_link(src, dst)
            if success:
                print(f"Link {src} → {dst} removed successfully")
            else:
                print(f"Error: Link not found")
        except Exception as e:
            print(f"Error: {str(e)}")
    
    def do_add_flow(self, arg):
        """Add a flow to the network: add_flow <src> <dst> [priority] [bandwidth]"""
        try:
            args = arg.strip().split()
            if len(args) < 2:
                print("Error: Source and destination nodes required")
                return
                
            src, dst = args[0], args[1]
            priority = int(args[2]) if len(args) > 2 else 0
            bandwidth = int(args[3]) if len(args) > 3 else 1
            
            flow = self.controller.add_flow(src, dst, priority, bandwidth)
            if flow:
                print(f"Flow added successfully: {flow}")
                print(f"  Primary Path: {' → '.join(flow.path)}")
                if flow.backup_path:
                    print(f"  Backup Path: {' → '.join(flow.backup_path)}")
                else:
                    print("  No backup path available")
            else:
                print(f"Error: Could not add flow (nodes might not exist or no path available)")
        except Exception as e:
            print(f"Error: {str(e)}")
    
    def do_remove_flow(self, arg):
        """Remove a flow from the network: remove_flow <flow_id>"""
        try:
            flow_id = int(arg.strip())
            success = self.controller.remove_flow(flow_id)
            if success:
                print(f"Flow {flow_id} removed successfully")
            else:
                print(f"Error: Flow {flow_id} not found")
        except Exception as e:
            print(f"Error: {str(e)}")
    
    def do_simulate_failure(self, arg):
        """Simulate a link failure: simulate_failure <src> <dst>"""
        try:
            args = arg.strip().split()
            if len(args) < 2:
                print("Error: Source and destination nodes required")
                return
                
            src, dst = args[0], args[1]
            success = self.controller.simulate_link_failure(src, dst)
            if success:
                print(f"Link failure simulated: {src} → {dst}")
            else:
                print(f"Error: Link not found")
        except Exception as e:
            print(f"Error: {str(e)}")
    
    def do_show_flows(self, arg):
        """Show all flows in the network"""
        self.controller.print_flows()
    
    def do_show_topology(self, arg):
        """Show the network topology"""
        self.controller.print_topology()
    
    def do_show_flow_tables(self, arg):
        """Show flow tables for all switches"""
        self.controller.print_flow_tables()
    
    def do_show_stats(self, arg):
        """Show controller statistics"""
        self.controller.print_statistics()
    
    def do_exit(self, arg):
        """Exit the program"""
        print("Exiting SDN Controller CLI")
        return True
        
    def do_quit(self, arg):
        """Exit the program"""
        return self.do_exit(arg)
    
    def emptyline(self):
        """Do nothing on empty line"""
        pass

def create_sample_topology(controller):
    """Create a sample topology for testing"""
    print("Creating sample topology...")
    
    # Add nodes
    controller.add_node("s1")
    controller.add_node("s2")
    controller.add_node("s3")
    controller.add_node("s4")
    controller.add_node("s5")
    controller.add_node("s6")
    
    # Add links
    controller.add_link("s1", "s2", 10, 1, 1)
    controller.add_link("s1", "s3", 5, 2, 2)
    controller.add_link("s2", "s4", 10, 1, 1)
    controller.add_link("s2", "s5", 5, 2, 2)
    controller.add_link("s3", "s5", 10, 1, 1)
    controller.add_link("s4", "s6", 10, 1, 1)
    controller.add_link("s5", "s6", 5, 2, 2)
    
    print("Sample topology created successfully!")

def main():
    """Main entry point for the SDN Controller application"""
    print("Starting SDN Controller...")
    
    # Create the controller
    controller = SDNController()
    
    # Create sample topology
    create_sample_topology(controller)
    
    # Add some flows
    print("Creating sample flows...")
    controller.add_flow("s1", "s6", 5, 2)
    controller.add_flow("s3", "s4", 2, 1)
    print("Sample flows created successfully!")
    
    # Display the topology
    controller.print_topology()
    
    # Start the CLI
    cli = SDNControllerCLI(controller)
    cli.cmdloop()

if __name__ == "__main__":
    main()