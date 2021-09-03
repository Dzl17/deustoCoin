from secrets import token_bytes
from coincurve import PublicKey
from sha3 import keccak_256

def generateKeys():
    private_key = keccak_256(token_bytes(32)).digest()
    public_key = PublicKey.from_valid_secret(private_key).format(compressed=False)[1:]
    address = keccak_256(public_key).digest()[-20:]
    return {'address': address.hex(), 'key': private_key.hex()}


def name(contract):
    return contract.functions.name().call()


def symbol(contract):
    return contract.functions.symbol().call()


def decimals(contract):
    return contract.functions.symbol().call()


def totalSuply(contract):
    return contract.functions.totalSupply().call()


def balanceOf(contract, address):
    return contract.functions.balanceOf(address).call()


def roleOf(contract, address):
    return contract.functions.roleOf(address).call()


def allowance(contract, owner, spender):
    return contract.functions.allowance(owner, spender).call()


def assignRole(w3, contract, caller, callerKey, account, roleID):
    transaction = contract.functions.assignRole(
        account, roleID
    ).buildTransaction({
        'gas': 10000000,
        'gasPrice': w3.toWei(w3.eth.gas_price, 'gwei'),
        'from': caller,
        'nonce': w3.eth.getTransactionCount(caller)
    })
    signed_tx = w3.eth.account.signTransaction(transaction, private_key=callerKey)
    return w3.eth.sendRawTransaction(signed_tx.rawTransaction)


def transfer(w3, contract, caller, callerKey, to, value):
    transaction = contract.functions.transfer(
        to, value
    ).buildTransaction({
        'gas': 10000000,
        'gasPrice': w3.toWei(w3.eth.gas_price, 'gwei'),
        'from': caller,
        'nonce': w3.eth.getTransactionCount(caller)
    })
    signed_tx = w3.eth.account.signTransaction(transaction, private_key=callerKey)
    return w3.eth.sendRawTransaction(signed_tx.rawTransaction)


def transferFrom(w3, contract, caller, callerKey, fromAcc, to, value):
    transaction = contract.functions.transferFrom(
        fromAcc, to, value
    ).buildTransaction({
        'gas': 10000000,
        'gasPrice': w3.toWei(w3.eth.gas_price, 'gwei'),
        'from': caller,
        'nonce': w3.eth.getTransactionCount(caller)
    })
    signed_tx = w3.eth.account.signTransaction(transaction, private_key=callerKey)
    return w3.eth.sendRawTransaction(signed_tx.rawTransaction)


def approve(w3, contract, caller, callerKey, spender, value):
    transaction = contract.functions.approve(
        spender, value
    ).buildTransaction({
        'gas': 10000000,
        'gasPrice': w3.toWei(w3.eth.gas_price, 'gwei'),
        'from': caller,
        'nonce': w3.eth.getTransactionCount(caller)
    })
    signed_tx = w3.eth.account.signTransaction(transaction, private_key=callerKey)
    return w3.eth.sendRawTransaction(signed_tx.rawTransaction)


def mint(w3, contract, caller, callerKey, to, value):
    transaction = contract.functions.mint(
        to, value
    ).buildTransaction({
        'gas': 10000000,
        'gasPrice': w3.toWei(w3.eth.gas_price, 'gwei'),
        'from': caller,
        'nonce': w3.eth.getTransactionCount(caller)
    })
    signed_tx = w3.eth.account.signTransaction(transaction, private_key=callerKey)
    return w3.eth.sendRawTransaction(signed_tx.rawTransaction)


def burn(w3, contract, caller, callerKey, fromAcc, value):
    transaction = contract.functions.burn(
        fromAcc, value
    ).buildTransaction({
        'gas': 10000000,
        'gasPrice': w3.toWei(w3.eth.gas_price, 'gwei'),
        'from': caller,
        'nonce': w3.eth.getTransactionCount(caller)
    })
    signed_tx = w3.eth.account.signTransaction(transaction, private_key=callerKey)
    return w3.eth.sendRawTransaction(signed_tx.rawTransaction)


def addAction(w3, contract, caller, callerKey, actionID, campaignID, reward):
    transaction = contract.functions.addAction(
        actionID, campaignID, reward
    ).buildTransaction({
        'gas': 10000000,
        'gasPrice': w3.toWei(w3.eth.gas_price, 'gwei'),
        'from': caller,
        'nonce': w3.eth.getTransactionCount(caller)
    })
    signed_tx = w3.eth.account.signTransaction(transaction, private_key=callerKey)
    return w3.eth.sendRawTransaction(signed_tx.rawTransaction)


def removeAction(w3, contract, caller, callerKey, actionID):
    transaction = contract.functions.removeAction(
        actionID
    ).buildTransaction({
        'gas': 10000000,
        'gasPrice': w3.toWei(w3.eth.gas_price, 'gwei'),
        'from': caller,
        'nonce': w3.eth.getTransactionCount(caller)
    })
    signed_tx = w3.eth.account.signTransaction(transaction, private_key=callerKey)
    return w3.eth.sendRawTransaction(signed_tx.rawTransaction)


def processAction(w3, contract, caller, callerKey, promoter, to, actionID, factor, time, ipfsHash):
    transaction = contract.functions.processAction(
        promoter, to, actionID, factor, time, ipfsHash
    ).buildTransaction({
        'gas': 10000000,
        'gasPrice': w3.toWei(w3.eth.gas_price, 'gwei'),
        'from': caller,
        'nonce': w3.eth.getTransactionCount(caller)
    })
    signed_tx = w3.eth.account.signTransaction(transaction, private_key=callerKey)
    return w3.eth.sendRawTransaction(signed_tx.rawTransaction)