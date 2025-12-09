---
title: ROS 2 Launch, Parameters, and Tools
sidebar_position: 3
---

# ROS 2 Launch, Parameters, and Tools

## Introduction

This chapter covers essential ROS 2 functionalities: the launch system for orchestrating multiple nodes, the parameter system for dynamic configuration, and a suite of command-line tools for monitoring and debugging your robotic applications. Mastering these aspects is crucial for developing and maintaining complex ROS 2 systems.

## Learning Outcomes

By the end of this chapter, you will be able to:
- Create and use ROS 2 launch files to start multiple nodes and configure parameters.
- Define and manage ROS 2 parameters programmatically and via the command line.
- Utilize key ROS 2 command-line tools for inspecting, logging, and debugging.

## Key Concepts

- **ROS 2 Launch System**: A mechanism for easily starting and managing multiple ROS 2 nodes and their configurations.
- **ROS 2 Parameters**: Configuration values that can be changed dynamically at runtime or set via launch files.
- **ROS 2 Command-Line Tools**: Utilities like `ros2 topic`, `ros2 node`, `ros2 param`, `ros2 service`, and `ros2 bag` for interacting with a running ROS 2 system.

## Section 1: Orchestrating Nodes with ROS 2 Launch

ROS 2 launch files are Python scripts that allow you to define how to run your ROS 2 nodes, set their parameters, and manage their lifecycle.

### Beginner Explanation

<details>
  <summary>For Beginners</summary>
  Imagine you have many robot parts that need to start at the same time and know how to work together. ROS 2 Launch is like a conductor for an orchestra, telling each part when to start and what music (settings) to play, so everything begins smoothly.
</details>

### Intermediate Explanation

<details>
  <summary>For Intermediate Learners</summary>
  ROS 2 launch files provide powerful features such as conditionals, loops, and substitutions, enabling complex system startup configurations. Understanding `launch_ros` actions for node lifecycle management and group actions for modularity is key.
</details>

### Advanced Explanation

<details>
  <summary>For Advanced Learners</summary>
  Advanced launch techniques involve integrating with containerization (e.g., Docker), orchestrating distributed systems across multiple machines, and dynamically generating launch configurations based on system state. Exploring custom launch actions and integrating with CI/CD pipelines are also critical for large-scale deployments.
</details>

### Urdu Translation

<details>
  <summary>اردو ترجمہ (Urdu Translation)</summary>
  آر او ایس 2 لانچ (ROS 2 Launch) روبوٹ کے بہت سے حصوں کو ایک ساتھ شروع کرنے اور انہیں بتانے میں مدد کرتا ہے کہ کیسے مل کر کام کرنا ہے۔ یہ ایک منظم طریقے سے سب کو شروع کرتا ہے، جیسے ایک آرکیسٹرا کا کنڈکٹر تمام سازوں کو بجانا شروع کرنے کا اشارہ دیتا ہے تاکہ سب کچھ ٹھیک سے ہو۔
</details>

### Agent Skills / Claude Subagent Hooks

<details>
  <summary>Agent Hooks</summary>
  {{AGENT_HOOKS}}
</details>

## Section 2: Dynamic Configuration with ROS 2 Parameters

Parameters allow you to configure nodes dynamically without recompiling the code.

### Parameter Declaration and Usage

Nodes can declare parameters, and their values can be set from launch files, YAML files, or the command line.

### Dynamic Reconfigure

Some parameters can be dynamically reconfigured at runtime, allowing for live adjustments to node behavior.

## Section 3: ROS 2 Command-Line Tools for Debugging

A rich set of command-line tools helps you interact with and debug your ROS 2 system.

### `ros2 run`, `ros2 launch`

For executing individual nodes and launch files.

### `ros2 node`, `ros2 topic`, `ros2 service`, `ros2 action`

For introspecting the graph (listing nodes, topics, services, actions, and their types).

### `ros2 param`

For getting, setting, and dumping parameters.

### `ros2 bag`

For recording and replaying message data.

### `rqt_` tools

Graphical tools for visualization and introspection (e.g., `rqt_graph`, `rqt_console`).

## Practical Tasks / Hands-on Exercises

1.  **Task 1**: Create a ROS 2 Launch File
    ```python
    # Create a launch file that starts a talker and listener node from `demo_nodes_cpp` package.
    # Set a parameter for the talker node via the launch file.
    ```
2.  **Task 2**: Experiment with ROS 2 Parameters
    ```bash
    # Use `ros2 param set` and `ros2 param get` to change and retrieve a parameter value of a running node.
    # Observe the change in the node's behavior.
    ```

## Summary

This chapter equipped you with the knowledge to effectively launch, configure, and debug your ROS 2 applications. You can now use launch files for orchestration, parameters for flexible configuration, and various command-line tools for introspection.

## Review Questions

1.  What is the primary purpose of a ROS 2 launch file, and why is it preferred over manually running nodes?
2.  How can you set a ROS 2 parameter from a launch file, and what are the benefits of using parameters?
3.  Name three useful ROS 2 command-line tools and describe their functions.

## References

1.  ROS 2 Launch System: [https://docs.ros.org/en/humble/How-To-Guides/Launch-files-overview.html](https://docs.ros.org/en/humble/How-To-Guides/Launch-files-overview.html)
2.  ROS 2 Parameters: [https://docs.ros.org/en/humble/Concepts/About-Parameters.html](https://docs.ros.org/en/humble/Concepts/About-Parameters.html)
3.  ROS 2 CLI Tools: [https://docs.ros.org/en/humble/Tutorials/Beginner-CLI-Tools/index.html](https://docs.ros.org/en/humble/Tutorials/Beginner-CLI-Tools/index.html)
