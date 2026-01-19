# BotKiller Protocol

BotKiller is a global, decentralized P2P protocol for **Unstoppable AI**: no central server, no corporate control, no single point of censorship.

The goal is to coordinate anonymous participants into a network that can execute, verify, and route AI workloads in a way that becomes **stronger and cheaper as adoption grows**.

## Core Concept: Unstoppable AI

Traditional AI depends on centralized providers (servers, accounts, policies, region locks, and deplatforming risk). BotKiller flips the model:

- AI execution is distributed across independent nodes.
- Verification is performed by economically-aligned auditors.
- Pricing is abstracted into credits for users, while long-term network value accrues to the token.

If the internet exists, BotKiller can exist.

## Network Roles

### Workers (Compute Providers)

Workers provide compute power to execute AI tasks.

- They receive tasks from the network.
- They return results.
- They are rewarded based on usage demand.

### Auditors (Fiscals)

Auditors verify results and help keep the network honest.

- Auditors stake the network token (BOKI) to qualify.
- Staking creates an economic cost for dishonest behavior.
- Validations can be recorded on-chain to create a permanent audit trail.

## Credits and BOKI (The Network Token)

BotKiller separates **user experience** from **network incentives**:

- Users pay for AI usage using **credits** (a user-facing unit designed for predictable pricing).
- Network growth, security, and verification increase the utility and value of **BOKI**.

As the network scales, demand and security pressure can drive BOKI’s role as the incentive backbone of the protocol.

## Smart Contract

- `BotKillerToken.sol` implements the BOKI token.
- The contract includes:
  - Fixed total supply
  - Founder allocation at launch
  - Basic staking for auditors
  - A minimal on-chain validation record (`ValidationRecorded` event)

## Support the Revolution

Early donors are supporting the birth of an uncontrollable, distributed intelligence.

The landing page (`index.html`) includes a MetaMask donation flow that sends POL to the verified on-chain address.

## GitHub Pages

This repository is GitHub Pages–ready.

- The site entry point is `index.html`.
- No build step is required.
