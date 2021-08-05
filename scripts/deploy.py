#!/usr/bin/python3

from brownie import Lottery, accounts


def main():
    return Lottery.deploy({'from': accounts[0]})
