# Satellite Detumbling

### detumble Module
This module provides functions for satellite detumbling using magnetorquers. It includes vector math utilities and the main dipole calculation for attitude control.

### Vector Math Utilities

#### Function: `dot_product`
Computes the dot product of two 3-element vectors.

##### Arguments
- **vector1** (tuple): First vector (length 3).
- **vector2** (tuple): Second vector (length 3).

##### Returns
- **float**: The dot product of the two vectors.

```py title="detumble.py"
def dot_product(vector1: tuple, vector2: tuple) -> float:
    return sum([a * b for a, b in zip(vector1, vector2)])
```

#### Function: `x_product`
Computes the cross product of two 3-element vectors.

##### Arguments
- **vector1** (tuple): First vector (length 3).
- **vector2** (tuple): Second vector (length 3).

##### Returns
- **list**: The cross product vector (length 3).

```py title="detumble.py"
def x_product(vector1: tuple, vector2: tuple) -> list:
    return [
        vector1[1] * vector2[2] - vector1[2] * vector2[1],
        vector1[0] * vector2[2] - vector1[2] * vector2[0],
        vector1[0] * vector2[1] - vector1[1] * vector2[0],
    ]
```

#### Function: `gain_func`
Returns the gain value for the detumble control law.

##### Returns
- **float**: Gain value (default 1.0).

```py title="detumble.py"
def gain_func():
    return 1.0
```

### Magnetorquer Dipole Calculation

#### Function: `magnetorquer_dipole`
Calculates the required dipole moment for the magnetorquers to detumble the satellite.

##### Arguments
- **mag_field** (tuple): The measured magnetic field vector (length 3).
- **ang_vel** (tuple): The measured angular velocity vector (length 3).

##### Returns
- **list**: The dipole moment vector to be applied (length 3).

```py title="detumble.py"
def magnetorquer_dipole(mag_field: tuple, ang_vel: tuple) -> list:
    gain = gain_func()
    scalar_coef = -gain / pow(dot_product(mag_field, mag_field), 0.5)
    dipole_out = x_product(mag_field, ang_vel)
    for i in range(3):
        dipole_out[i] *= scalar_coef
    return dipole_out
```
