#!/bin/bash

sudo isula rm -f $(sudo isula ps --filter 'label=com.nestnet' -a -q)
sudo ./mn -c