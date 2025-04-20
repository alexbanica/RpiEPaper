#!/usr/bin/python
# -*- coding:utf-8 -*-
import argparse

ARG_RENDERER_TYPE_CONSOLE = 'console'
ARG_RENDERER_TYPE_EPAPER = 'epaper'
ARG_RENDERER_CHOICES = [ARG_RENDERER_TYPE_CONSOLE, ARG_RENDERER_TYPE_EPAPER]


class ServerStatusArgumentParser:
    @staticmethod
    def parse():
        parser = argparse.ArgumentParser(description='Server Status Display')
        parser.add_argument('-r', '--renderer', choices=ARG_RENDERER_CHOICES, default=ARG_RENDERER_TYPE_EPAPER,
                            help='Choose renderer type: console or epaper')
        
        return parser.parse_args()
