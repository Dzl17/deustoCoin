from secrets import token_bytes
from coincurve import PublicKey
from sha3 import keccak_256
from web3 import Web3
import os


def generate_keys():
    """Return a new random ethereum address with its private key."""
    private_key = keccak_256(token_bytes(32)).digest()
    public_key = PublicKey.from_valid_secret(private_key).format(compressed=False)[1:]
    address = keccak_256(public_key).digest()[-20:]
    return {'address': '0x' + address.hex(), 'key': private_key.hex()}


class BlockchainManager():
    def __init__(self) -> None:
        self.w3 = Web3(Web3.HTTPProvider(os.environ.get('BLOCKCHAIN_URL')))
        
        abi = open('contractABI.txt').read()
        self.contract = self.w3.eth.contract(address=Web3.toChecksumAddress(os.environ.get('CONTRACT_ADDRESS')), abi=abi)
        
        transfer_filter = self.contract.events.Transfer.build_filter()
        transfer_filter.fromBlock = 0
        self.transfer_filter_instance = transfer_filter.deploy(self.w3)

        action_filter = self.contract.events.Action.build_filter()
        action_filter.fromBlock = 0
        self.action_filter_instance = action_filter.deploy(self.w3)


    def get_all_transfers(self) -> list:
        """Returns all transfer logs saved in the blockchain."""
        return self.transfer_filter_instance.get_all_entries()


    def get_all_transfer_events(self) -> list:
        """Returns all the filtered tranfer events, showing only the event values."""
        new_list = []
        for i in self.get_all_transfers():
            new_list.append(i.args)
        return new_list


    def get_all_actions(self) -> list:
        """Returns all action logs saved in the blockchain."""
        return self.action_filter_instance.get_all_entries()


    def get_all_action_events(self) -> list:
        """Returns all the filtered action events, showing only the event values."""
        new_list = []
        for i in self.get_all_actions():
            new_list.append(i.args)
        return new_list


    def name(self):
        """Get the name of the coin."""
        return self.contract.functions.name().call()


    def symbol(self):
        """Get the symbol of the coin."""
        return self.contract.functions.symbol().call()


    def decimals(self):
        """Get in how many decimals the coin is divided. Deustocoin has 2 decimals, to resemble the Euro."""
        return self.contract.functions.decimals().call()


    def total_supply(self):
        """Returns the total supply of the coin."""
        return self.contract.functions.totalSupply().call()


    def balance_of(self, address):
        """Returns the balance of the input address."""
        return self.contract.functions.balanceOf(address).call()


    def transfer(self, caller, caller_key, to, value):
        """Allows a user to transfer their balance to another user."""
        transaction = self.contract.functions.transfer(
            to, int(value)
        ).buildTransaction({
            'gas': 10000000,
            'gasPrice': self.w3.toWei(self.w3.eth.gas_price, 'gwei'),
            'from': caller,
            'nonce': self.w3.eth.getTransactionCount(caller, 'pending')
        })
        signed_tx = self.w3.eth.account.signTransaction(transaction, private_key=caller_key)
        return self.w3.eth.sendRawTransaction(signed_tx.rawTransaction)


    def mint(self, caller, caller_key, to, value):
        """Allows an administrator to mint/generate an amount of coins to the 'to' address."""
        transaction = self.contract.functions.mint(
            to, int(value)
        ).buildTransaction({
            'gas': 10000000,
            'gasPrice': self.w3.toWei(self.w3.eth.gas_price, 'gwei'),
            'from': caller,
            'nonce': self.w3.eth.getTransactionCount(caller, 'pending')
        })
        signed_tx = self.w3.eth.account.signTransaction(transaction, private_key=caller_key)
        return self.w3.eth.sendRawTransaction(signed_tx.rawTransaction)


    def burn(self, caller, caller_key, from_acc, value):
        """Allows an administrator to burn/delete and amount of coins from the 'from_acc' address."""
        transaction = self.contract.functions.burn(
            from_acc, int(value)
        ).buildTransaction({
            'gas': 10000000,
            'gasPrice': self.w3.toWei(self.w3.eth.gas_price, 'gwei'),
            'from': caller,
            'nonce': self.w3.eth.getTransactionCount(caller, 'pending')
        })
        signed_tx = self.w3.eth.account.signTransaction(transaction, private_key=caller_key)
        return self.w3.eth.sendRawTransaction(signed_tx.rawTransaction)


    def processAction(self, caller, caller_key, promoter, to, action_id, reward, time, ipfs_hash):
        """Registers a collaborator's good action on the blockchain and gives them credit for its completion."""
        transaction = self.contract.functions.processAction(
            promoter, to, action_id, reward, time, ipfs_hash
        ).buildTransaction({
            'gas': 10000000,
            'gasPrice': self.w3.toWei(self.w3.eth.gas_price, 'gwei'),
            'from': caller,
            'nonce': self.w3.eth.getTransactionCount(caller, 'pending')
        })
        signed_tx = self.w3.eth.account.signTransaction(transaction, private_key=caller_key)
        return self.w3.eth.sendRawTransaction(signed_tx.rawTransaction)