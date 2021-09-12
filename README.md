# DeustoCoin

Adaptation to Smart Contracts and Hyperledger Besu of [Deustocoin, by Jorge El Busto](https://github.com/bu5to/deustoCoin). Created for MORElab from Deusto University.

Deustocoin is a project that intends to promote the motto "Blockchain for Good" and contribute to a better world through a social coin using the emerging technology that is Blockchain.


## How does it work?

The web application works as follows: 

Both members of the university and promoters of campaigns belonging to external companies can operate on the app. The promoters can create campaigns and actions that intend to comply with the [United Nations' SDGs (Sustainable Development Goals)](https://sdgs.un.org/goals). Examples of those actions are using recyclable coffee cups or walking/cycling to the university instead of using a car. They can monitor the Key Performance Indicators (KPIs) of the campaigns and actions, and observe their progress on graphics.

Members of the university, referred to as 'collaborators', can then complete those actions to earn a reward in UDCoin, a cryptocurrency based on the Ethereum ERC20 standard (more details below). This coin can then be exchanged for offers created by the companies, such as food, drinks, or discounts on other products; it can also be sent to other collaborators.

Some users may be administrators, to manage and watch over the usage of the system.


## Technical aspects

The web app is written in [Flask](https://flask.palletsprojects.com/en/2.0.x/), a Python framework. The communication with the blockchain is done trhough the [Python version of Web3](https://web3py.readthedocs.io/en/stable/). Other technologies used are IPFS (used to save action realization proofs) or Google App Engine (to carry out authentication).

In the original project, the coins where based on the ether token and sent using raw transactions on the blockchain. In this fork, the system has been redesigned to rely on a Solidity Smart Contract, which can be read in [contracts/deustocoin.sol](contracts/deustocoin.sol). This contract is compliant with the Ethereum [ERC20 Token Standard](https://ethereum.org/en/developers/docs/standards/tokens/erc-20/). This contract can be deployed on the Ethereum network, but a different approach is being tested and explored, based on [Hyperledger Besu](https://www.hyperledger.org/use/besu).

Besu is an Ethereum client developed by the Linux Foundation that supports the creation of private and permissioned networks. As it has been previously mentioned, this application tries to comply with the UN's Sustainable Development Goals, an intention which is not currently compatible with the high energy usage of blockchains like Ethereum or Bitcoin. That is why for now the plan is to deploy the system in a smaller network that uses the [Proof of Authority](https://en.wikipedia.org/wiki/Proof_of_authority) consensus protocol, which consumes a lot less energy and works better with our approach. Besu also supports gas-free networks (with no transaction fees) which greatly improves the final user experience.

This way, the web app would be deployed on a centralized server, while the currency management would be carried out in a decentralized blockchain, combining the best of both worlds.


## Cloud deployment
The original application is currently [deployed in Heroku](https://deustocoin.herokuapp.com), without the use of smart contracts or Besu.
