from secrets import token_bytes
from coincurve import PublicKey
from sha3 import keccak_256
from web3 import Web3
import os

contract=None

def init_contract(web3):
    """Initialize the smart contract."""
    abi = open('contractABI.txt').read()
    global contract
    contract = web3.eth.contract(address=Web3.toChecksumAddress(os.environ.get('CONTRACT_ADDRESS')), abi=abi)


def generate_keys():
    """Return a new random ethereum address with its private key."""
    private_key = keccak_256(token_bytes(32)).digest()
    public_key = PublicKey.from_valid_secret(private_key).format(compressed=False)[1:]
    address = keccak_256(public_key).digest()[-20:]
    return {'address': '0x' + address.hex(), 'key': private_key.hex()}


def name():
    """Get the name of the coin."""
    return contract.functions.name().call()


def symbol():
    """Get the symbol of the coin."""
    return contract.functions.symbol().call()


def decimals():
    """Get in how many decimals the coin is divided. Deustocoin has 2 decimals, to resemble the Euro."""
    return contract.functions.decimals().call()


def total_supply():
    """Returns the total supply of the coin."""
    return contract.functions.totalSupply().call()


def balance_of(address):
    """Returns the balance of the input address."""
    return contract.functions.balanceOf(address).call()


def role_of(address):
    """Returns the role of the input address (Collaborator, Promoter or Administrator)."""
    return contract.functions.roleOf(address).call()


def allowance(owner, spender):
    """Returns the amount the spender is allowed to withdraw from the owner balance."""
    return contract.functions.allowance(owner, spender).call()


def assign_role(w3, caller, callerKey, account, roleID):
    """Allows an Administrator to change the role of a user."""
    transaction = contract.functions.assignRole(
        account, roleID
    ).buildTransaction({
        'gas': 10000000,
        'gasPrice': w3.toWei(w3.eth.gas_price, 'gwei'),
        'from': caller,
        'nonce': w3.eth.getTransactionCount(caller, 'pending')
    })
    signed_tx = w3.eth.account.signTransaction(transaction, private_key=callerKey)
    return w3.eth.sendRawTransaction(signed_tx.rawTransaction)


def transfer(w3, caller, callerKey, to, value):
    """Allows a user to transfer their balance to another user."""
    transaction = contract.functions.transfer(
        to, int(value)
    ).buildTransaction({
        'gas': 10000000,
        'gasPrice': w3.toWei(w3.eth.gas_price, 'gwei'),
        'from': caller,
        'nonce': w3.eth.getTransactionCount(caller, 'pending')
    })
    signed_tx = w3.eth.account.signTransaction(transaction, private_key=callerKey)
    return w3.eth.sendRawTransaction(signed_tx.rawTransaction)


def transfer_from(w3, caller, callerKey, fromAcc, to, value):
    """Allows a user to transfer to themselves an amount of coins limited by the allowance they have over that user's balance."""
    transaction = contract.functions.transferFrom(
        fromAcc, to, int(value)
    ).buildTransaction({
        'gas': 10000000,
        'gasPrice': w3.toWei(w3.eth.gas_price, 'gwei'),
        'from': caller,
        'nonce': w3.eth.getTransactionCount(caller, 'pending')
    })
    signed_tx = w3.eth.account.signTransaction(transaction, private_key=callerKey)
    return w3.eth.sendRawTransaction(signed_tx.rawTransaction)


def approve(w3, caller, callerKey, spender, value):
    """Allows the spender to withdraw the input amount of coins from the caller accont."""
    transaction = contract.functions.approve(
        spender, int(value)
    ).buildTransaction({
        'gas': 10000000,
        'gasPrice': w3.toWei(w3.eth.gas_price, 'gwei'),
        'from': caller,
        'nonce': w3.eth.getTransactionCount(caller, 'pending')
    })
    signed_tx = w3.eth.account.signTransaction(transaction, private_key=callerKey)
    return w3.eth.sendRawTransaction(signed_tx.rawTransaction)


def mint(w3, caller, callerKey, to, value):
    """Allows an administrator to mint/generate an amount of coins to the 'to' address."""
    transaction = contract.functions.mint(
        to, int(value)
    ).buildTransaction({
        'gas': 10000000,
        'gasPrice': w3.toWei(w3.eth.gas_price, 'gwei'),
        'from': caller,
        'nonce': w3.eth.getTransactionCount(caller, 'pending')
    })
    signed_tx = w3.eth.account.signTransaction(transaction, private_key=callerKey)
    return w3.eth.sendRawTransaction(signed_tx.rawTransaction)


def burn(w3, caller, callerKey, fromAcc, value):
    """Allows an administrator to burn/delete and amount of coins from the 'fromAcc' address."""
    transaction = contract.functions.burn(
        fromAcc, int(value)
    ).buildTransaction({
        'gas': 10000000,
        'gasPrice': w3.toWei(w3.eth.gas_price, 'gwei'),
        'from': caller,
        'nonce': w3.eth.getTransactionCount(caller, 'pending')
    })
    signed_tx = w3.eth.account.signTransaction(transaction, private_key=callerKey)
    return w3.eth.sendRawTransaction(signed_tx.rawTransaction)


def emit_action(w3, caller, callerKey, promoter, to, actionID, reward, time, ipfs_hash, proof_url):
    """Registers a collaborator's good action on the blockchain and gives them credit for its completion."""
    transaction = contract.functions.processAction(
        promoter, to, actionID, reward, time, ipfs_hash, proof_url
    ).buildTransaction({
        'gas': 10000000,
        'gasPrice': w3.toWei(w3.eth.gas_price, 'gwei'),
        'from': caller,
        'nonce': w3.eth.getTransactionCount(caller, 'pending')
    })
    signed_tx = w3.eth.account.signTransaction(transaction, private_key=callerKey)
    return w3.eth.sendRawTransaction(signed_tx.rawTransaction)