import numpy as np
from scipy.special import gamma
from user_input import InputData
from dataclasses import dataclass

@dataclass
class CalculationResults:
    """
    Data container for the results of the wind energy simulation.

    Attributes
    ----------
    rated_speed : float
        Minimum wind speed at which rated power is reached [m/s].
    cut_out : float
        Wind speed above which the turbine shuts down for safety [m/s].
    rated_power : float
        Maximum electrical power output [kW].
    cut_in : float
        Wind speed below which there is not enough energy to start [m/s].
    generated_energy : float
        Total annual energy production [MWh].
    average_power : float
        Average power output over the year [kW].
    full_load_hours : float
        Equivalent hours of operation at rated power [h].
    aerodynamical_load : float
        Thrust force on the rotor at rated speed [kN].
    solidity : float
        Ratio of blade area to swept area [%].
    storm_load : float
        Wind load on the stationary structure during a storm (60 m/s) [kN].
    wall_thickness_operation : float
        Required tower wall thickness for normal operating loads [m].
    wall_thickness_storm : float
        Required tower wall thickness for storm loads [m].
    """
    rated_speed: float # [m/s] minimum speed when rated power reached
    cut_out: float # [m/s] speeds above -> turn off
    rated_power: float # [kW] maximum power 
    cut_in: float # [m/s] speeds beneith -> turn off
    generated_energy: float # [MWh] total generated power
    average_power: float # [kWh] average won power
    full_load_hours: float # [h] comparison number (how often under fully load)
    aerodynamical_load: float # [kN] force under full load
    solidity: float # [%] blades area / swept area
    storm_load: float # [kN] load under storm
    wall_thickness_operation: float  # [m] wall thickness required for normal operations
    wall_thickness_storm: float # [m] wall thickness required for storm

class EnergyCalculations:
    """
    Physics engine for calculating wind energy production and physical loads.

    Parameters
    ----------
    input_data : InputData
        Object containing turbine dimensions and environmental parameters.

    Attributes
    ----------
    input_data : InputData
        The source input data.
    z0 : float
        Roughness length [m].
    wind_nacelle : float
        Average wind speed at hub height [m/s].
    output_data : CalculationResults
        Stored results after calling calculate().
    """
    def __init__(self, input_data: InputData):
        self.update(input_data)
        self.output_data: CalculationResults

    def update(self, input_data: InputData):
        """
        Update the simulation with new input data and recalculate hub-height wind.

        Parameters
        ----------
        input_data : InputData
            The new input data object.
        """
        self.input_data = input_data

        self.z0 = self.input_data.roughness/1000
        self.wind_nacelle = (
            self.input_data.avg_U10* 
            np.log(self.input_data.height/self.z0)/
            np.log(10/self.z0)
        ) # From formula

        self.calculate()

    def calculate(self) -> CalculationResults:
        """
        Perform the full suite of energy and load calculations.

        Calculates Weibull distribution, applies Betz law approximations,
        determines operational speeds, integrates energy production,
        and estimates structural loads.

        Returns
        -------
        CalculationResults
            A dataclass containing all calculated physical and energy metrics.
        """
        h = 1 # step value. Increase for better resolution
        wind_speeds = np.arange(1, 61, h)

        # Calculate distrobution
        k = self.input_data.k_factor
        C = self.wind_nacelle/ gamma(1+1/k) # C constant gives characteristic windspeed 
        distrobution= (k/C)* (wind_speeds/C)**(k-1)*np.exp(-(wind_speeds/C)**k)

        # Hours of the year
        possible_hours = distrobution*8760
        availability = (100-self.input_data.downtime)/100
        available_hours = availability*possible_hours

        # Energies
        energy_per_m2 = 0.62*wind_speeds**3*possible_hours/1000 # KWh/m^2
        tot_possible_energy_per_m2 = np.sum(energy_per_m2)
        cumulated_energy = np.cumsum(energy_per_m2)


        # Steps below to cap cumulated energy to simulate effect of Betz law
        # Finds first index where cumulated_energy surpasses limit 
        effective_limit = tot_possible_energy_per_m2/3
        rated_mask = cumulated_energy > effective_limit
        idx = np.argmax(rated_mask) 
        cumulated_energy_rated = cumulated_energy.copy()
        rated_speeds = wind_speeds.copy() # Effective windspeeds        
        if cumulated_energy[idx] > effective_limit:
            # Changes values after and at index to value before 
            cumulated_energy_rated[idx:] = cumulated_energy_rated[idx] if idx > 0 else 0
            rated_speeds[idx:] = rated_speeds[idx] if idx > 0 else 0
            rated_speed = rated_speeds[idx]

        # capped by turn off limit
        turn_off_limit = 0.8*tot_possible_energy_per_m2
        capped_velocities = wind_speeds.copy() # array for velocities before WEC is turned off
        capped_mask = cumulated_energy > turn_off_limit
        idx = np.argmax(capped_mask)
        cut_out = capped_velocities[idx]
        if capped_mask[-1] != 0: # It shouldn't be all zeros
            capped_velocities[idx:] = capped_velocities[idx]
            velocity_cap = capped_velocities[idx]
        
        swept_area = np.pi*(self.input_data.diam/2)**2

        cut_in = int(rated_speed * 0.01**(1/3)*10)/10 # [m/s] speeds below are to slow
        # [kW] the maximum power reached 
        rated_power = 0.62*rated_speed**3*swept_area*self.input_data.capture_efficiency*self.input_data.efficiency_drivetrain/1000 

        conditions = [
            wind_speeds <= cut_in, # values below cut_in, therefore set to 0 below
            (wind_speeds > cut_in) & (wind_speeds <= rated_speed), # variable energies
            (wind_speeds > rated_speed) & (wind_speeds <=cut_out), # Between rated and cut_out, therefore constant
            wind_speeds >cut_out, # values above cut_out
        ]

        alternatives = [
            0, # Shut off, zone 1
            energy_per_m2*swept_area*self.input_data.capture_efficiency*self.input_data.efficiency_drivetrain, # zone 2
            rated_power*available_hours, # zone 3, Since between rated and cutout. Energy output will just be rated_power*available_hours. Constant.
            0, # zone 4, Shut off
        ]

        generated_energies = np.select(conditions, alternatives) # Energy for different windspeeds in kWh

        generated_energy = np.sum(generated_energies)/1000 # Total energy per year in MWh


        # C_T=8/9, 1.2 from density of air.
        aerodynamical_load = 1/2*1.2*8/9*swept_area*rated_speed**2/1000 # [kN] force excerted on tower from wind


        solidity = 3 #! [%] antal blad * bladens bredd / rotorns radie Hur ändra denna? Ska den vara output eller input? 
        storm_load = 1/2*1.2*1.5*solidity/100*swept_area*60**2/1000 #  @60 [kN], max at 60 kN. load under storm

        wall_thickness_operation = aerodynamical_load*self.input_data.height/(np.pi*(self.input_data.height/40)**2*160)*2
        wall_thickness_storm=storm_load*self.input_data.height/(np.pi*(self.input_data.height/40)**2*160)*2

        # Set values to remember
        self.output_data = CalculationResults(
            rated_speed, cut_out, rated_power, cut_in, generated_energy, 
            average_power = generated_energy/8.76, # [KWh], 8.76 from hours in year / 1000
            full_load_hours = generated_energy/rated_power*1000, # [h], energy produced relative to maximum capacity
            aerodynamical_load = aerodynamical_load,
            solidity = solidity, #! [%] antal blad * bladens bredd / rotorns radie Hur ändra denna? Ska den vara output eller input? 
            storm_load = storm_load, #  @60 [kN], max at 60 kN. load under storm
            wall_thickness_operation = wall_thickness_operation,
            wall_thickness_storm = wall_thickness_storm
        )
        return self.output_data

if __name__ == "__main__":
    input_data = InputData(name="Kalle Kula", SSN="199903151234", diam=37, height=44)
    energy_calculations = EnergyCalculations(input_data)
    energy_calculations.calculate()
    print(energy_calculations.output_data.storm_load)


