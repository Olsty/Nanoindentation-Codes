import numpy as np
import matplotlib.pyplot as plt 
import pandas as pd
import math
from openpyxl import load_workbook
#IMPORTANT NOTE: A column = depth, B column is load
#Row 1 should be the headers


#These the purpose of these general lists is to combine data if the function is ran multiple times
general_yield_stress_data = []
general_yield_stress_data_2um = []
general_yield_stress_data_10um = []
general_yield_strain_data = []
general_yp_contact_radius_data = []
general_yp_contact_radius_data_2um = []
general_yp_contact_radius_data_10um = []


def spynach(input_files, 
            peak_load,
            Reff,
            output_name,
            output_path):
    
    yield_stress_data1 = []
    yield_strain_data1 = []
    yp_contact_radius_data1 = []
    yield_stress_data2 = []
    yield_strain_data2 = []
    yp_contact_radius_data2 = []
    yield_stress_data3 = []
    yield_strain_data3 = []
    yp_contact_radius_data3 = []   
    plt.figure(figsize=(20, 12))
    file_names = []
    for i in input_files:
        excel_file = i
        file_names.append(i)
        print(i)
        yp_location1 = 0
        
    # =============================================================================
    #     Importing excel file
    # =============================================================================
    # By using the Pandas library, the load-depth data is imported in this section
    
        depth_data = pd.read_excel(excel_file, usecols=[0])
        depth_data = depth_data.to_numpy().flatten()
        load_data = pd.read_excel(excel_file, usecols=[1])
        load_data = load_data.to_numpy().flatten()
        
        max_load = np.argmax(load_data)
        depth_data_loading=depth_data[:max_load + 1]
        load_data_loading=load_data[:max_load + 1]
    
    # =============================================================================
    #     Data processing
    # =============================================================================
    # In this section, the unloading part of the load-depth curve is sliced away
    # and "jump-bakcs" of indentation depth are removed
    
        if max(load_data) >= peak_load:
            load_data_loading = []
            depth_data_loading = []
            for location, value in enumerate(load_data):
                if value < peak_load:
                    load_data_loading.append(load_data[location])
                    depth_data_loading.append(depth_data[location])
                    continue
                load_data_loading.append(load_data[location])
                depth_data_loading.append(depth_data[location])
                break
        else:
            max_load = np.argmax(load_data)
            depth_data_loading=depth_data[:max_load + 1]
            load_data_loading=load_data[:max_load + 1]
        
        valid_values = []
        previous_value = 0
        for i, depth in enumerate(depth_data_loading):
            if depth >= previous_value:
                valid_values.append(i)
                previous_value = depth
        valid_load = []
        valid_depth = []
        for i in valid_values:
            valid_load.append(load_data_loading[i])
            valid_depth.append(depth_data_loading[i])
        depth_data_loading = np.array(valid_depth)
        load_data_loading = np.array(valid_load)
        
    # =============================================================================
    # Stress & strain calculation
    # =============================================================================
    # This section calculates the stress and strain from the load-depth data
    
        stress_data = []
        strain_data=[]
        for location,depth in enumerate(depth_data_loading):
            if depth == 0:
                continue
            a = math.sqrt(Reff*depth)
            stress = load_data_loading[location]/(math.pi*pow(a,2))
            strain = depth/(2.4*a)
            stress_data.append(stress)
            strain_data.append(strain)
        stress_data = np.array(stress_data)
        strain_data = np.array(strain_data)
        
    # =============================================================================
    # Determining yield point method 1 (the point slope method, PSM)
    # =============================================================================
    # In this section, the point slope method is applied
    # To change the parameters, the change constants in line 118 and 120 can be adjusted 
        
        if Reff == 10:
            change_constant = 3.475
        if Reff == 2:
            change_constant = 10
        slope_change_ratios = []
        strain_data_for_average_slopes = []
        valid_locations = [] 
        invalid_locations = []
        for location, stress in enumerate(stress_data):
            if location == 0:
                invalid_locations.append(location)
                continue
            if location == (len(stress_data)-1):
                break 
            dy1 = stress_data[location] - stress_data[location-1]
            dy2 = stress_data[location+1] - stress_data[location]
            dx1 = strain_data[location] - strain_data[location-1]
            dx2 = strain_data[location+1] - strain_data[location]
            if dx1 == 0 or dx2 == 0:
                invalid_locations.append(location-1)
                continue
            slope_before = dy1/dx1
            slope_after = dy2/dx2
            if slope_before == 0 :
                invalid_locations.append(location-1)
                continue
            change_ratio = (slope_after-slope_before)/slope_before
            slope_change_ratios.append(change_ratio)
            strain_data_for_average_slopes.append(strain_data[location])
            valid_locations.append(location-1)
        change_in_change_ratio = []
        for location, ratio in enumerate(slope_change_ratios[1:]):
            if slope_change_ratios[location-1] == 0:
                continue
            change_ratio = (slope_change_ratios[location] - slope_change_ratios[location-1])/slope_change_ratios[location-1]
            change_in_change_ratio.append(change_ratio)
        for location, ratio in enumerate(slope_change_ratios):
            if ratio > change_constant or ratio < -change_constant:
                if location == 0:
                    continue
                yp_location1 = valid_locations[location]
                yield_stress_data1.append(stress_data[location])
                print(f"Yield point PSM {stress_data[location]} GPa")
                yield_strain_data1.append(strain_data[location])
                if Reff == 2:
                    general_yield_stress_data_2um.append(stress_data[location])
                if Reff == 10:
                    general_yield_stress_data_10um.append(stress_data[location])
                general_yield_strain_data.append(strain_data[location])
                break
        else:
            print("No yield point was found by using the PSM")
             
    # =============================================================================
    # Determining yield point method 2 (the interval slope method, ISM)
    # ============================================================================= 
    # In this section, the interval slope method is applied
    # To change the parameters, the change constants in line 276 and 278 can be adjusted 
    
        slope_data4 = []
        for location, value in enumerate(stress_data):
            if location == 0:
                if (strain_data[location]-strain_data[location-5]) == 0:
                    slope = (stress_data[location]-stress_data[location-5])/((1.000001*strain_data[location+5])-strain_data[location])
                    slope_data4.append(slope)
                    continue
                slope = (stress_data[location+5]-stress_data[location])/(strain_data[location+5]-strain_data[location])
                slope_data4.append(slope)
                continue
            if location == 1:
                if (strain_data[location]-strain_data[location-5]) == 0:
                    slope = (stress_data[location]-stress_data[location-5])/((1.000001*strain_data[location+5])-strain_data[location-1])
                    slope_data4.append(slope)
                    continue
                slope = (stress_data[location+5]-stress_data[location-1])/(strain_data[location+5]-strain_data[location-1])
                slope_data4.append(slope)
                continue
            if location == 2:
                if (strain_data[location]-strain_data[location-5]) == 0:
                    slope = (stress_data[location]-stress_data[location-5])/((1.000001*strain_data[location+5])-strain_data[location-2])
                    slope_data4.append(slope)
                    continue
                slope = (stress_data[location+5]-stress_data[location-2])/(strain_data[location+5]-strain_data[location-2])
                slope_data4.append(slope)
                continue
            if location == 3:
                if (strain_data[location]-strain_data[location-5]) == 0:
                    slope = (stress_data[location]-stress_data[location-5])/((1.000001*strain_data[location+5])-strain_data[location-3])
                    slope_data4.append(slope)
                    continue
                slope = (stress_data[location+5]-stress_data[location-3])/(strain_data[location+5]-strain_data[location-3])
                slope_data4.append(slope)
                continue
            if location == 4:
                if (strain_data[location]-strain_data[location-5]) == 0:
                    slope = (stress_data[location]-stress_data[location-5])/((1.000001*strain_data[location+5])-strain_data[location-4])
                    slope_data4.append(slope)
                    continue
                slope = (stress_data[location+5]-stress_data[location-4])/(strain_data[location+5]-strain_data[location-4])
                slope_data4.append(slope)
                continue
            
            if location == (len(stress_data)-5):
                if (strain_data[location]-strain_data[location-5]) == 0:
                    slope = (stress_data[location]-stress_data[location-5])/((1.000001*strain_data[location+4])-strain_data[location-5])
                    slope_data4.append(slope)
                    continue
                slope = (stress_data[location+4]-stress_data[location-5])/(strain_data[location+4]-strain_data[location-5])
                slope_data4.append(slope)
                continue
            if location == (len(stress_data)-4):
                if (strain_data[location]-strain_data[location-5]) == 0:
                    slope = (stress_data[location]-stress_data[location-5])/((1.000001*strain_data[location+3])-strain_data[location-5])
                    slope_data4.append(slope)
                    continue
                slope = (stress_data[location+3]-stress_data[location-5])/(strain_data[location+3]-strain_data[location-5])
                slope_data4.append(slope)
                continue
            if location == (len(stress_data)-3):
                if (strain_data[location]-strain_data[location-5]) == 0:
                    slope = (stress_data[location]-stress_data[location-5])/((1.000001*strain_data[location+2])-strain_data[location-5])
                    slope_data4.append(slope)
                    continue
                slope = (stress_data[location+2]-stress_data[location]-5)/(strain_data[location+2]-strain_data[location-5])
                slope_data4.append(slope)
                continue
            if location == (len(stress_data)-2):
                if (strain_data[location]-strain_data[location-5]) == 0:
                    slope = (stress_data[location]-stress_data[location-5])/((1.000001*strain_data[location+1])-strain_data[location-5])
                    slope_data4.append(slope)
                    continue
                slope = (stress_data[location+1]-stress_data[location-5])/(strain_data[location+1]-strain_data[location-5])
                slope_data4.append(slope)
                continue
            if location == (len(stress_data)-1):
                if (strain_data[location]-strain_data[location-5]) == 0:
                    slope = (stress_data[location]-stress_data[location-5])/((1.000001*strain_data[location])-strain_data[location-5])
                    slope_data4.append(slope)
                    continue
                slope = (stress_data[location]-stress_data[location-5])/(strain_data[location]-strain_data[location-5])
                slope_data4.append(slope)
                continue
            if (strain_data[location+5]-strain_data[location-5]) == 0:
                slope = (stress_data[location+5]-stress_data[location-5])/((1.000001*strain_data[location+5])-strain_data[location-5])
                slope_data4.append(slope)
                continue
            slope = (stress_data[location+5]-stress_data[location-5])/(strain_data[location+5]-strain_data[location-5])
            slope_data4.append(slope)
        change_over_strain_change =[]
        for location, value in enumerate(slope_data4):
            if location == 0:
                change_over_strain_change.append(0)
                continue
            if (strain_data[location]-strain_data[location - 1]) == 0:
                change_over_strain_change.append(abs(((slope_data4[location]-slope_data4[location-1])/slope_data4[location-1])/((1.000001*strain_data[location])-strain_data[location-1])))
                continue
            else:
                change_over_strain_change.append(abs(((slope_data4[location]-slope_data4[location-1])/slope_data4[location-1])/(strain_data[location]-strain_data[location-1])))
        if Reff == 10:
            change_constant2 = 194
        if Reff == 2:
            change_constant2 = 484
        for location, i in enumerate(change_over_strain_change):
            if i >= change_constant2:   
                yp_location2 = location
                break
        yield_stress_data2.append(stress_data[yp_location2])
        print(f"Yield point ISM {stress_data[yp_location2]} GPa")
        yield_strain_data2.append(strain_data[yp_location2])
        general_yield_stress_data.append(stress_data[yp_location2])
        if Reff == 2:
            general_yield_stress_data_2um.append(stress_data[yp_location2])
        if Reff == 10:
            general_yield_stress_data_10um.append(stress_data[yp_location2])
        general_yield_strain_data.append(strain_data[yp_location2])                  
        plt.plot(strain_data, stress_data, c = "b", lw=0.5, alpha = 0.4)
        valid_strain = []
        for i in valid_locations:
            valid_strain.append(strain_data[i])
            
    # =============================================================================
    # Determining yield point method 3 (the elastic deviation method)
    # =============================================================================  
    # In this section, the elastic deviation method is applied
    # One can adjust the way the linear (y = a*x+b) line is calculated in this section
    
        if Reff == 10:
            halfway_yp = int(yp_location2*0.85)
            a1_1 = (stress_data[halfway_yp-2]-stress_data[5])/(strain_data[halfway_yp-2]-strain_data[5])
            a1_2 = (stress_data[halfway_yp-1]-stress_data[5])/(strain_data[halfway_yp-1]-strain_data[5])
            a1_3 = (stress_data[halfway_yp]-stress_data[5])/(strain_data[halfway_yp]-strain_data[5])
            a1_4 = (stress_data[halfway_yp+1]-stress_data[5])/(strain_data[halfway_yp+1]-strain_data[5])
            a1_5 = (stress_data[halfway_yp+2]-stress_data[5])/(strain_data[halfway_yp+2]-strain_data[5])
            a2_1 = (stress_data[halfway_yp-2]-stress_data[6])/(strain_data[halfway_yp-2]-strain_data[6])
            a2_2 = (stress_data[halfway_yp-1]-stress_data[6])/(strain_data[halfway_yp-1]-strain_data[6])
            a2_3 = (stress_data[halfway_yp]-stress_data[6])/(strain_data[halfway_yp]-strain_data[6])
            a2_4 = (stress_data[halfway_yp+1]-stress_data[6])/(strain_data[halfway_yp+1]-strain_data[6])
            a2_5 = (stress_data[halfway_yp+2]-stress_data[6])/(strain_data[halfway_yp+2]-strain_data[6])
            a3_1 = (stress_data[halfway_yp-2]-stress_data[7])/(strain_data[halfway_yp-2]-strain_data[7])
            a3_2 = (stress_data[halfway_yp-1]-stress_data[7])/(strain_data[halfway_yp-1]-strain_data[7])
            a3_3 = (stress_data[halfway_yp]-stress_data[7])/(strain_data[halfway_yp]-strain_data[7])
            a3_4 = (stress_data[halfway_yp+1]-stress_data[7])/(strain_data[halfway_yp+1]-strain_data[7])
            a3_5 = (stress_data[halfway_yp+2]-stress_data[7])/(strain_data[halfway_yp+2]-strain_data[7]) 
            a = (a1_1+a1_2+a1_3+a1_4+a1_5+a2_1+a2_2+a2_3+a2_4+a2_5+a3_1+a3_2+a3_3+a3_4+a3_5)/15
            b = stress_data[halfway_yp] - (a*strain_data[halfway_yp])
            deviations = []
            for location, value in enumerate(strain_data):
                expected_value = (a*strain_data[location])+b
                deviation = (stress_data[location]-expected_value)/expected_value
                deviations.append(deviation)              
            for location, value in enumerate(deviations):
                if all(i < 0 for i in deviations[location:]):
                    yp_location3 = location
                    plt.scatter(strain_data[yp_location3], stress_data[yp_location3], marker = "X", s=20, c = "black")
                    yield_stress_data3.append(stress_data[yp_location3])
                    yield_strain_data3.append(strain_data[yp_location3])
                    print(f"Yield point EDM {stress_data[yp_location3]} GPa")
                    general_yield_stress_data.append(stress_data[yp_location3])
                    general_yield_stress_data_10um.append(stress_data[yp_location3])
                    general_yield_strain_data.append(strain_data[yp_location3])
                    break
        if Reff == 2:
            halfway_yp = int(yp_location2-5)
            a6_1 = (stress_data[halfway_yp-3]-stress_data[5])/(strain_data[halfway_yp-3]-strain_data[5])
            a6_2 = (stress_data[halfway_yp-2]-stress_data[5])/(strain_data[halfway_yp-2]-strain_data[5])
            a6_3 = (stress_data[halfway_yp-1]-stress_data[5])/(strain_data[halfway_yp-1]-strain_data[5])
            a6_4 = (stress_data[halfway_yp]-stress_data[5])/(strain_data[halfway_yp]-strain_data[5])
            a6_5 = (stress_data[halfway_yp+1]-stress_data[5])/(strain_data[halfway_yp+1]-strain_data[5])
            a6_6 = (stress_data[halfway_yp+2]-stress_data[5])/(strain_data[halfway_yp+2]-strain_data[5])
            a6_7 = (stress_data[halfway_yp+3]-stress_data[5])/(strain_data[halfway_yp+3]-strain_data[5])
            a7_1 = (stress_data[halfway_yp-3]-stress_data[6])/(strain_data[halfway_yp-3]-strain_data[6])
            a7_2 = (stress_data[halfway_yp-2]-stress_data[6])/(strain_data[halfway_yp-2]-strain_data[6])
            a7_3 = (stress_data[halfway_yp-1]-stress_data[6])/(strain_data[halfway_yp-1]-strain_data[6])
            a7_4 = (stress_data[halfway_yp]-stress_data[6])/(strain_data[halfway_yp]-strain_data[6])
            a7_5 = (stress_data[halfway_yp+1]-stress_data[6])/(strain_data[halfway_yp+1]-strain_data[6])
            a7_6 = (stress_data[halfway_yp+2]-stress_data[6])/(strain_data[halfway_yp+2]-strain_data[6])
            a7_7 = (stress_data[halfway_yp+3]-stress_data[6])/(strain_data[halfway_yp+3]-strain_data[6])
            a8_1 = (stress_data[halfway_yp-3]-stress_data[7])/(strain_data[halfway_yp-3]-strain_data[7])
            a8_2 = (stress_data[halfway_yp-2]-stress_data[7])/(strain_data[halfway_yp-2]-strain_data[7])
            a8_3 = (stress_data[halfway_yp-1]-stress_data[7])/(strain_data[halfway_yp-1]-strain_data[7])
            a8_4 = (stress_data[halfway_yp]-stress_data[7])/(strain_data[halfway_yp]-strain_data[7])
            a8_5 = (stress_data[halfway_yp+1]-stress_data[7])/(strain_data[halfway_yp+1]-strain_data[7])
            a8_6 = (stress_data[halfway_yp+2]-stress_data[7])/(strain_data[halfway_yp+2]-strain_data[7])
            a8_7 = (stress_data[halfway_yp+3]-stress_data[7])/(strain_data[halfway_yp+3]-strain_data[7])
            a = (a6_1 + a6_2 + a6_3 + a6_4 + a6_5 + a6_6 + a6_7 + a7_1 + a7_2 + a7_3 + a7_4 + a7_5 +a7_6 + a7_7 + a8_1 + a8_2 +a8_3 + a8_4 + a8_5 + a8_6 +a8_7)/21
            b1 = stress_data[halfway_yp-3] - (a*strain_data[halfway_yp-3])
            b2 = stress_data[halfway_yp-2] - (a*strain_data[halfway_yp-2])
            b3 = stress_data[halfway_yp-1] - (a*strain_data[halfway_yp-1])
            b4 = stress_data[halfway_yp] - (a*strain_data[halfway_yp])
            b5 = stress_data[halfway_yp+1] - (a*strain_data[halfway_yp+1])
            b6 = stress_data[halfway_yp+2] - (a*strain_data[halfway_yp+2])
            b7 = stress_data[halfway_yp+3] - (a*strain_data[halfway_yp+3])
            b = (b1 + b2 + b3 + b4 + b5 + b6 + b7)/7
            deviations = []
            for location, value in enumerate(strain_data):
                expected_value = (a*strain_data[location])+b
                deviation = (stress_data[location]-expected_value)/expected_value
                deviations.append(deviation)
            for location, value in enumerate(deviations):
                if all(i < 0 for i in deviations[location:]):
                    yp_location3 = location - 1 
                    yield_stress_data3.append(stress_data[yp_location3])
                    yield_strain_data3.append(strain_data[yp_location3])
                    print(f"Yield point EDM {stress_data[yp_location3]} GPa")
                    general_yield_stress_data.append(stress_data[yp_location3])
                    general_yield_stress_data_2um.append(stress_data[yp_location3])
                    break
        plt.scatter(strain_data[yp_location3], stress_data[yp_location3], s=20, c = "#ffa54f")
        plt.scatter(strain_data[yp_location2], stress_data[yp_location2], s=20, c = "#CC79A7")

    # =============================================================================
    # Contact radius determination    
    # =============================================================================
    # The following section calculates the contact radius at the yield hardness from each method    
    
        if yp_location1 != 0: 
            yp_contact_radius_data1.append(math.sqrt(Reff*depth_data[yp_location1]))
            if Reff == 2:
                general_yp_contact_radius_data_2um.append(math.sqrt(Reff*depth_data[yp_location1]))
            if Reff == 10:
                general_yp_contact_radius_data_10um.append(math.sqrt(Reff*depth_data[yp_location1]))
        yp_contact_radius_data2.append(math.sqrt(Reff*depth_data[yp_location2]))
        general_yp_contact_radius_data.append(math.sqrt(Reff*depth_data[yp_location2]))
        if Reff == 2:
            general_yp_contact_radius_data_2um.append(math.sqrt(Reff*depth_data[yp_location2]))
        if Reff == 10:
            general_yp_contact_radius_data_10um.append(math.sqrt(Reff*depth_data[yp_location2]))
        yp_contact_radius_data3.append(math.sqrt(Reff*depth_data[yp_location3]))
        general_yp_contact_radius_data.append(math.sqrt(Reff*depth_data[yp_location3]))
        if Reff == 2:
            general_yp_contact_radius_data_2um.append(math.sqrt(Reff*depth_data[yp_location3]))
        if Reff == 10:
            general_yp_contact_radius_data_10um.append(math.sqrt(Reff*depth_data[yp_location3]))
        print("")
    
    # =============================================================================
    #    Exporting data
    # =============================================================================
    # In the following section, the pop-in data is extracted to an .xlsx-file
    # If desired, one can add more lists to the table in line 422
    
    file_names2 = []
    for i in file_names:
        last_backslash_index = i.rfind("\\")
        file_names2.append(i[last_backslash_index + 1:])
    table = {
        "File name": file_names2,
        "Yield stress PSM (GPa)": yield_stress_data1,
        "Contact radius PSM (μm)": yp_contact_radius_data1,
        "Yield stress ISM (GPa)": yield_stress_data2,
        "Contact radius ISM (μm)": yp_contact_radius_data2,
        "Yield stress EDM (GPa)": yield_stress_data3,
        "Contact radius EDM (μm)": yp_contact_radius_data3
    }
    output_table = pd.DataFrame(table)
    path = f"{output_path}\{output_name}.xlsx"    
    with pd.ExcelWriter(f"{output_name}.xlsx") as writer:
        output_table.to_excel(writer)
        output_table.to_excel(path, index = False)
    workbook = load_workbook(path)
    worksheet = workbook["Sheet1"]
    for col in ['B', 'C', 'D', 'E', 'F', 'G']:
        worksheet.column_dimensions[col].width = 27  
    for col in ['A']:
        worksheet.column_dimensions[col].width = 60  
    workbook.save(path)

    # =============================================================================
    # Plotting
    # =============================================================================
    # In this section, plots and histrograms containing data about the found yield hardnesses are created
    
    plt.plot(strain_data, stress_data, c = "b", lw=0.5, alpha = 0.4)
    plt.xlabel("Strain (ε)", fontsize= 20)
    plt.ylabel("Stress (GPa)", fontsize= 20)
    plt.xticks(fontsize=18)
    plt.yticks(fontsize=18)
    plt.plot(0,0, label = "Stress-strain curve", c = "b")
    plt.scatter([], [], label = "Yield point ISM", c = "#CC79A7", s= 60)
    plt.scatter([], [], label = "Yield point EDM", c = "#ffa54f", s= 60)
    plt.legend(loc = "upper left", fontsize = 20)
        
    plt.figure()
    plt.title("Yield stress distribution")
    plt.hist(general_yield_stress_data, bins = 20, color = "blue", edgecolor = "black")
    plt.xlabel("Yield stress (GPa)")
    plt.ylabel("Frequency")
    
    plt.figure()
    plt.title("Yield stress distribution PSM")
    plt.hist(yield_stress_data1, color = "blue", edgecolor = "black", bins = 20)
    plt.xlabel("Yield stress (GPa)")
    plt.ylabel("Frequency")
    
    plt.figure()
    plt.title("Yield stress distribution ISM")
    plt.hist(yield_stress_data2, color = "blue", edgecolor = "black")
    plt.xlabel("Yield stress (GPa)")
    plt.ylabel("Frequency")
    
 
    plt.figure()
    plt.title("Yield stress distribution EDM")
    plt.hist(yield_stress_data3 , color = "blue", edgecolor = "black")
    plt.xlabel("Yield stress (GPa)")
    plt.ylabel("Frequency")
    
    
    plt.figure(figsize = (20, 12))
    plt.scatter(general_yp_contact_radius_data_2um, general_yield_stress_data_2um, c = "blue", label = "2 μm tip")
    plt.scatter(general_yp_contact_radius_data_10um, general_yield_stress_data_10um, c = "orange", label = "10 μm tip")
    plt.title("Yield stress to contact radius", fontsize = 25)
    plt.xlabel("Contact radius (μm)", fontsize= 20)
    plt.ylabel("Yield stress (GPa)", fontsize= 20)
    plt.xticks(fontsize=18)
    plt.yticks(fontsize=18)
    plt.legend(fontsize= 20)
    
    plt.figure(figsize = (20, 12))
    plt.scatter(general_yp_contact_radius_data, general_yield_stress_data, c = "blue")
    plt.title("Yield stress to contact radius", fontsize = 25)
    plt.xlabel("Contact radius (μm)", fontsize= 20)
    plt.ylabel("Yield stress (GPa)", fontsize= 20)  
    plt.xticks(fontsize=18)
    plt.yticks(fontsize=18)
    
    
    plt.figure(figsize = (20, 12))
    plt.scatter(yield_stress_data2, yield_stress_data3, c = "blue")
    plt.title("Yield stress ISM to yield stress EDM", fontsize = 25)
    plt.xlabel("Yield stress ISM (GPa)", fontsize= 20)
    plt.ylabel("Yield stress EDM (GPa)", fontsize= 20)  
    plt.xticks(fontsize=18)
    plt.yticks(fontsize=18)
        
    print("Tadaa!")
    
    return

input_10um = []
# =============================================================================
#     An example how to run Spynach
# =============================================================================
# list_with_input_files = [r"C:\Users\Documents\Research Nanoindentation Research\input_file1.xlsx,
#                          r"C:\Users\Documents\Research Nanoindentation Research\input_file2.xlsx,
#                          r"C:\Users\Documents\Research Nanoindentation Research\input_file3.xlsx
# ]    
#
# spynach(input_files = list_with_input_files, 
#         peak_load = 450, 
#         Reff = 10,
#         output_name = "Spynach data 10 um",
#         output_path = r"C:\Users\Documents\Research Nanoindentation Research")
# Note: peak_load is in mN and Reff in μm

