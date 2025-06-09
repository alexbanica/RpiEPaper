#!/usr/bin/python
# -*- coding:utf-8 -*-

from dataclasses import dataclass

@dataclass
class ClusterHatStatus:
    is_on: bool
    has_alert: bool
    active_node_count: int