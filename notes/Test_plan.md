# Objective

This document summarizes the key objectives and actionable items for testing the LX20 Leak Detection system based on Synergi Pipeline Simulator (SPS).

The objectives are:

1. The various components of the model is functional as it was intended to be by design, i.e. Functional Testing.

2. The overall model performance is acceptable for leak detection, i.e. Performance Testing.

# Requirements

The data flow of the model can be summarized as:

SCADA -> Redundancy Logics -> Hydraulics Model -> Imbalance Logics -> Alarm Logics -> SCADA display

The performance of the system can be assess based on the output of:
- Hydraulics Model:
    - Assess whether the diagnostic flow from each monitors are minimize by the setup.
- Imbalance Logics:
    - Assess whether imbalance stay within Baseline Threshold during non-leak scenarios for various averaging windows
    - Assess whether imbalance exceeds Baseline Threshold during leak scenarios for various averaging windows
- Alarm Logics:
    - Assess true alarm rate based on the final threshold logic
    - Assess false alarm rate based on the final threshold logic
    
Baseline Threshold here refers to a predefined threshold we agreed to do the analysis on.

## Functional Testing

The focus is on the functional integrity of each individual component of the system. Specifically:

- Redundancy Logics:
    - Redundant pressure and temperature transmitter logics function as they were designed: priority queue for each pressure monitor and temperature painting point, and fall back to a hydraulically stable value when no measurement is available.

- Hydraulics Model:
    - Pump station start and shutdown logics: station by-pass logic during shutdown and disable by-pass when starting up.

- Expand/collapse logics: verify that leak sections expand and collapse according to the pump station flow meter statuses.

- Alarm logics to SCADA display: verify that the map is complete and accurate.

## Performance Testing

- Diagnostic Flow:
    - Ensure diagnostic flow is minimized during non-leak scenarios for all flow paths:
        - CSHSP to HSTNT
        - CSHSP to NDRLD
        - LIBRT to PTNCI
        - PLNPN to PTNCI
        - LIBRT to LUCAS
        - LIBRT to HSTNL
        - LIBRT to PTNCI
        - LIBRT to CITGO
        - HRDSY to HRTFD
        - HRDSY to PTOKA
    - Ensure diagnostic flow is minimized during swings: 
        - NDLPS swing to NDRLD
        - NDLPS swing from NDRLD
        - STLCT Swing to STLCTB
        - STLCT Swing from STLCTB

- Imbalance Logics:
    - Compare imbalance statistics on a two-hour averaging window to a pre-defined threshold during steady-state running condition. 

- Alarm Logics:
    - False alarm statistics during non-leak scenarios 
    - Time-to-alarm for leak scenarios.


# Testing tool

The testing tool is designed to run testing scenarios in parallel, maximizing the utilization of computational resources available, to perform functional and performance testing. There are two main components of the tool:

1. Kick off simulation runs in parallel until the termination condition has been met.
2. Monitor and collect simulation results for KPI reporting.

## Inputs to the testing tool:

- json file summarizing all scenarios: 
    - Each of the functional and performance scenario above is captured as a scenario
    - Parametric runs of each scenario is also available for all pokable variables in SPS.

- RTU data files:
    - Azure Blob Container is the primary host location of RTU data files.
    - Files can be moved from Azure Blob Container via a command line tool before submitting test runs.

## Outputs from the testing tool:

- This part is currently under development. The idea is:
    - After the testing tool submits all scenarios, a separate worker will be initialized to monitor active runs using the py_sps module, provided by standard SPS installation. It will continuously parse the .review file to estimate execution time per simulation time step and stream desired results to a result summary file.
    - SQL Light is used to capture the output of the testing runs.
    - Perform post-run analytics and report on run performance - possibly also utilizing the Azure blob container.

