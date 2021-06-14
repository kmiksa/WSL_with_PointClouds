Repo for MSc in Data Science thesis at University of Amsterdam : 'Weakly Supervised Learning using Signals from Point Clouds"

# detections

## Start developing

### 1. build docker
```bash
$ docker build -t tf-worker .
```

### 2. [OPTION 1] run detector

Use the `detector` command in docker:

```bash
$ docker run tf-worker detector 
```

### 2. [OPTION 2] run tracker

Use the `tracker` command in docker:

```bash
$ docker run tf-worker tracker 
```