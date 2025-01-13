## Overview

UNav Server provides a serverless implementation for indoor navigation using computer vision techniques. It leverages Modal for deployment and offers features like visual localization, path planning, and navigation guidance.

## Prerequisites

- Python 3.8+
- Modal CLI
- A Modal account and token
- Required Python packages (specified in `modal_requirements.txt`)

## Deployment

Navigate to the `src` folder

``` cd src
```

```
modal deploy modal_functions/unav.py
```



## Test the deployed unav code

Make sure you are inside the `src` folder

``` python modal_functions/test_modal_function.py

```
