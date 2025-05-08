# Basic SDN Controller

A Python-based Software-Defined Networking (SDN) controller implementation that demonstrates the core concepts of SDN including network topology management, flow management, and traffic engineering.

## Features

- Network topology management (add/remove nodes and links)
- Path computation with priority-based routing
- Flow table generation and management
- Link failure simulation and recovery
- Backup path computation for resilience
- Command-line interface for interactive control

## Usage

### Running the Controller

Simply run the Python script:

```
python sdn_controller.py
```

This will initialize the controller with a sample topology (6 switches and interconnecting links), create some example flows, and start the command-line interface.

### Command-Line Interface

The controller provides a command-line interface for interacting with the network:

| Command | Description | Example |
|---------|-------------|---------|
| `add_node <node_id>` | Add a new switch to the network | `add_node s7` |
| `remove_node <node_id>` | Remove a switch from the network | `remove_node s7` |
| `add_link <src> <dst> [capacity] [weight] [delay]` | Add a link between switches | `add_link s1 s7 10 1 1` |
| `remove_link <src> <dst>` | Remove a link from the network | `remove_link s1 s7` |
| `add_flow <src> <dst> [priority] [bandwidth]` | Add a new flow | `add_flow s1 s7 5 2` |
| `remove_flow <flow_id>` | Remove a flow | `remove_flow 3` |
| `simulate_failure <src> <dst>` | Simulate a link failure | `simulate_failure s1 s2` |
| `show_flows` | Display all flows | `show_flows` |
| `show_topology` | Show network topology | `show_topology` |
| `show_flow_tables` | Show flow tables for all switches | `show_flow_tables` |
| `show_stats` | Show controller statistics | `show_stats` |
| `exit` or `quit` | Exit the program | `exit` |

## Implementation Details

### Traffic Engineering Policies

The controller implements the following traffic engineering policies:

1. **Priority-based path selection**: Higher priority flows (priority > 5) are routed along paths optimized for low delay
2. **Load balancing**: When multiple paths exist, flows are distributed based on current link utilization
3. **Resilience through backup paths**: Critical flows receive backup paths that avoid links in the primary path
4. **Automatic rerouting**: When links fail, affected flows are automatically rerouted using backup paths or newly computed paths

### Watermark Implementation

This implementation includes a cryptographic watermark based on the student ID as required:

```python
STUDENT_ID = "898927734"
HASH_TEXT = STUDENT_ID + "NeoDDaBRgX5a9"
WATERMARK = hashlib.sha256(HASH_TEXT.encode()).hexdigest()
```

This watermark influences design decisions such as:
- Using priority threshold of 5 for high-priority flows (inspired by "5a9" in the hash text)
- Path selection algorithms that incorporate the last two digits of the student ID

### Implementation Challenge

A significant challenge encountered during implementation was efficiently handling link failures without disrupting all flows in the network. The solution evolved from a naive approach that recalculated all paths to a more sophisticated approach that:

1. Identifies only the flows directly affected by the failure
2. Uses pre-computed backup paths for immediate recovery when available
3. Only computes new paths when necessary

This approach significantly reduces the impact of link failures on unaffected traffic and improves overall network resilience.

## Project Structure

- `sdn_controller.py`: Main controller implementation
- `README.md`: This documentation file

## License

This project is submitted for educational purposes only.
