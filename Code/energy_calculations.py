import numpy as np
from scipy.special import gamma
from user_input import InputData
from dataclasses import dataclass

@dataclass
class CalculationResults:
    """Output data from energy calculations"""
    rated_speed: float
    cut_out: float
    rated_power: float
    cut_in: float
    generated_energy: float
    average_power: float
    full_load_hours: float
    aerodynamical_load: float
    solidity: float
    storm_load: float
    wall_thickness_operation: float
    wall_thickness_storm: float

class EnergyCalculations:
    """Calculates energy data from input_data"""
    def __init__(self, input_data: InputData):
        self.update(input_data)
        self.output_data: CalculationResults

    def update(self, input_data: InputData):
        self.input_data = input_data

        self.z0 = self.input_data.roughness/1000
        self.wind_nacelle = (
            self.input_data.avg_U10* 
            np.log(self.input_data.height/self.z0)/
            np.log(10/self.z0)
        ) # From formula

        self.calculate()

    def calculate(self) -> CalculationResults:
        """Calculates various variables from input_data and add to self.output_data. Also outputs output_data
        In dataclass:
            rated_speed, cut_out, rated_power, cut_in, generated_energy, average_power, full_load_hours, aerodynamical_load, solidity, storm_load, wall_thickness_operation, wall_thickness_storm
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

        cut_in = int(rated_speed * 0.01**(1/3)*10)/10
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

        # Set values to remember
        self.output_data = CalculationResults(
            rated_speed, cut_out, rated_power, cut_in, generated_energy, 
            average_power = generated_energy/8.76, # [KWh], 8.76 from hours in year / 1000
            full_load_hours = generated_energy/rated_power*1000, # [h], energy produced relative to maximum capacity
            aerodynamical_load = 1/2*1.2*8/9*swept_area*rated_speed**2/1000,
            solidity = 3, #! [%] antal blad * bladens bredd / rotorns radie Hur ändra denna? Ska den vara output eller input? 
            storm_load = 1/2*1.2*1.5*self.solidity/100*swept_area*60**2/1000, #  @60 [kN], max at 60 kN. load under storm
            wall_thickness_operation = self.aerodynamical_load*self.input_data.height/(np.pi*(self.input_data.height/40)**2*160)*2,
            wall_thickness_storm= self.storm_load*self.input_data.height/(np.pi*(self.input_data.height/40)**2*160)*2
        )
        return self.output_data

if __name__ == "__main__":
    input_data = InputData(name="Kalle Kula", SSN="199903151234", diam=37, height=44)
    energy_calculations = EnergyCalculations(input_data)
    energy_calculations.calculate()
    print(energy_calculations.storm_load)


