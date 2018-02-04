# Multi-Machine-Ripper (mmr)

## Introduction

This project has the goal of becoming a fully automated **distributed** ripper and transcoder for CD, DVD, and Bluray discs.

Today basic distribution, transcoding, and collection of ripped video titles is functional, and is in active development.

## Example Run Command


`docker run -d
            --name mmr-prod
            --cpus="3.5"
            --network=host
            -v /data/incoming:/data/incoming
            -v /data/outgoing:/data/outgoing
            -v /data/log:/log
            -e "MMR_LEADER=<x.x.x.x>"
            scottessner/mmr:latest`

### Recommended parameters

**-d** - Run in daemon mode

**--name** - Set a name for keeping track of this container (optional)

**--cpus="3.5"** - Sets a limit on CPU usage for the container. HandBrake will use ALL the CPU available to it. This parameter will reserve some resources for other operations.  Values can be decimals, in units of CPU cores.

**--network=host** - Host networking is used because the nodes of the system utilize tcp connections for communication on dynamically assigned ports

**-e "MMR_LEADER=<x.x.x.x>"** - This environment variable tells a node where to find the convention leader.  Replace **<x.x.x.x>** with the ip address of your convention leader for every node.

## Volumes

#### /data/incoming
The incoming folder on the convention leader is watched for new files to transcode

#### /data/outgoing
The outgoing folder on the convention leader is the output folder for all transcoded files

#### /log
This folder contains a few key files for tracking status

**mmr.log** - General log file for the local node

**queue.txt** - (convention leader only) Current status of all transcoding jobs. This file is update every 3 seconds and can be monitored continuously using `watch -n 3 cat queue.txt`

**job_history.csv** - (convention leader only) Detailed history of all jobs in a raw state
