---
title: Robot Description with URDF
sidebar_position: 2
---

# Robot Description with URDF

## Introduction

This chapter delves into the Uniform Robot Description Format (URDF), an XML format used in ROS 2 to describe all aspects of a robot. You will learn how to define a robot's kinematic and dynamic properties, visualize it in various simulation environments, and understand the importance of an accurate robot model for effective control and simulation.

## Learning Outcomes

By the end of this chapter, you will be able to:
- Understand the structure and syntax of URDF files.
- Create a URDF model for a simple robot, defining its links and joints.
- Visualize URDF models in tools like `rviz2` and `gazebo`.

## Key Concepts

- **URDF**: XML format for describing robot kinematics, dynamics, visuals, and collision properties.
- **Link**: A rigid body part of the robot (e.g., base, arm segment, wheel).
- **Joint**: Connects two links, defining their relative motion (e.g., revolute, prismatic, fixed).
- **Kinematics**: Describes the motion of a robot without considering forces (forward and inverse).
- **Dynamics**: Describes the motion of a robot considering forces and torques.

## Section 1: Understanding URDF Structure

URDF files define a robot as a tree-like structure of links connected by joints.

### Beginner Explanation

<details>
  <summary>For Beginners</summary>
  Think of URDF as a detailed blueprint for your robot. It tells the computer exactly what your robot looks like, how big its parts are, and how those parts connect and move. This blueprint helps the computer imagine and control the robot in a virtual world.
</details>

### Intermediate Explanation

<details>
  <summary>For Intermediate Learners</summary>
  URDF allows for comprehensive robot modeling, including visual meshes for rendering, collision meshes for physics simulation, and inertial properties for dynamic calculations. Understanding the proper definition of coordinate frames and transformations between links is critical.
</details>

### Advanced Explanation

<details>
  <summary>For Advanced Learners</summary>
  Advanced URDF involves understanding xacro for modularity and reusability, SDF for more complex multi-robot and environment descriptions in Gazebo, and the interplay between URDF and SRDF (Semantic Robot Description Format) for motion planning. Parameterizing URDF models for different robot configurations is also a key skill.
</details>

### Urdu Translation

<details>
  <summary>اردو ترجمہ (Urdu Translation)</summary>
  یو آر ڈی ایف (URDF) روبوٹ کا ایک تفصیلی نقشہ ہے جو کمپیوٹر کو بتاتا ہے کہ روبوٹ کے تمام حصے کیسے نظر آتے ہیں، ان کا سائز کیا ہے، اور وہ آپس میں کیسے جڑے ہوئے ہیں اور کیسے حرکت کرتے ہیں۔ یہ نقشہ روبوٹ کو مجازی دنیا میں تصور کرنے اور کنٹرول کرنے میں مدد کرتا ہے۔
</details>

### Agent Skills / Claude Subagent Hooks

<details>
  <summary>Agent Hooks</summary>
  This section would contain hooks for AI agent integration, allowing for dynamic adaptation of URDF examples based on the learner's specific robot platform and learning objectives.
</details>

## Section 2: Creating a Simple URDF Model

Let's create a basic URDF for a two-wheeled robot.

### Defining Links

Each link is defined with its visual, collision, and inertial properties.

### Defining Joints

Joints connect links and specify their type (e.g., fixed, revolute, prismatic), axis of rotation/translation, and limits.

## Practical Tasks / Hands-on Exercises

1.  **Task 1**: Build a Basic Two-Link Robot URDF
    ```xml
    <!-- Create a simple URDF file for a robot with a base link and a single arm link connected by a revolute joint. -->
    <!-- Define visual, collision, and inertial properties for both links. -->
    ```
2.  **Task 2**: Visualize Your URDF in RViz2
    ```bash
    # Use `ros2 launch urdf_tutorial display.launch.py model:=<your_urdf_file.urdf>` to load and visualize your URDF in RViz2.
    # Experiment with joint state publishers to move the arm.
    ```

## Summary

This chapter provided an in-depth look at URDF, enabling you to describe and model robotic systems. You now understand how to define links, joints, and their properties, which is crucial for both simulation and real-world robot control.

## Review Questions

1.  Explain the difference between a link and a joint in URDF.
2.  Why are visual, collision, and inertial properties important for a robot model?
3.  How does URDF contribute to the simulation and control of a robot?

## References

1.  URDF Documentation: [http://wiki.ros.org/urdf](http://wiki.ros.org/urdf)
2.  ROS 2 URDF Tutorials: [https://docs.ros.org/en/humble/Tutorials/Intermediate/URDF/Building-a-Visual-Robot-Model-with-URDF-from-Scratch.html](https://docs.ros.org/en/humble/Tutorials/Intermediate/URDF/Building-a-Visual-Robot-Model-with-URDF-from-Scratch.html)
3.  XACRO for URDF: [http://wiki.ros.org/xacro](http://wiki.ros.org/xacro)
