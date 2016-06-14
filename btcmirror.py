#!/usr/bin/env python
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import sys
import pprint
import random
from bitcoinrpc.authproxy import AuthServiceProxy as ServiceProxy
from decimal import Decimal


"""
    We will be called from a walletnotify config setting with a
    TXID as our only commandline parameter.

    Mirror the transaction right back to the source. Since we'll be
    using the actual transaction as the input, we can do this with
    zero confirmations.

    Reqs:
     - A full bitcoin node that indexes all transactions (txindex=1)
"""


def main():
    access = ServiceProxy("http://username:password@127.0.0.1:8332")
    txid = sys.argv[1]
    # print txid
    txinfo = access.gettransaction(txid)
    pprint.pprint(txinfo)

    # Check the details to make sure it's an incoming transaction
    # Ensure everything is incoming, to avoid 
    # mirroring change/consolidation transactions.    
    myaddresses = set()
    for details in txinfo["details"]:
        # print details
        if details["category"] != "receive":
            return
        myaddresses.add(details["address"])

    tx = access.decoderawtransaction(txinfo["hex"])
    pprint.pprint(tx)
    # Now gather all the outputs to send back
    newtx_inputs = []
    total_amount = Decimal(0)
    for vout in tx["vout"]:
        for address in vout["scriptPubKey"]["addresses"]:
            if address in myaddresses:
                newtx_inputs.append({"txid":txid,"vout":vout["n"]})
                total_amount += vout["value"]
                break

    print newtx_inputs
    print total_amount
    
    # Now find the sendign addresses, and choose one at random
    # to receive the funds.
    total_inputs = Decimal("0")
    addresses = []
    for vin in tx["vin"]:
        intxid = vin["txid"]
        invout = vin["vout"]

        # Get the outputs of the input transaction
        intx = access.getrawtransaction(intxid,1)
        # print intxid, invout
        vout = intx["vout"][invout]
        # pprint.pprint(vout)
        total_inputs += vout["value"]
        addresses.extend(vout["scriptPubKey"]["addresses"])
    print "Total inputs: %f" % total_inputs
    print addresses
    to_address = random.choice(addresses)

    # Build a transaction with the output of the original transaction as input
    # and to_address as output.
    newtx_hex = access.createrawtransaction(newtx_inputs,{to_address:float(total_amount)})
    newtx_hex = access.signrawtransaction(newtx_hex)["hex"]
    print newtx_hex
    # print >>open("/home/user/a.txt","a"), access.decoderawtransaction(newtx_hex)
    access.sendrawtransaction(newtx_hex)


    #print access.getinfo()
    #print access.listreceivedbyaddress(6)

if __name__ == "__main__":
    main()
