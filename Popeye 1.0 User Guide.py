import numpy as np
import matplotlib.pyplot as plt 
import pandas as pd
from openpyxl import load_workbook
import math
#IMPORTANT NOTE: A column = depth, B column is load
#Row 1 should be the headers

#These the purpose of these general lists is to combine data if the function is ran multiple times
general_cumulative_popin_length_data = []
general_popin_load_data = []
general_popin_depth_data = []
general_popin_length_data = []
general_plastic_deformation_data = []
general_max_depth_data = []
general_popin_stress_data = []
general_popin_strain_data = []
general_popin_contact_radius_data = []

#In the next lines, Popeye defines the arguments (parameters) for the function
#The default values are also defined in these lines and thus can be adjusted here
def popeye(input_files, 
          Reff, 
          output_path, 
          peak_load,
          max_popin_length = 10, 
          name_output_excel = "Popin_data"):
    
    
    cumulative_popin_length_data = []
    sheet_counter = 1
    popin_counter = 0
    plt.figure(figsize=(20, 12))
    for i in input_files:
        excel_file = i
        
    # =============================================================================
    #     Importing excel file
    # =============================================================================
    
        depth_data = pd.read_excel(excel_file, usecols=[0])
        depth_data = depth_data.to_numpy().flatten()
        load_data = pd.read_excel(excel_file, usecols=[1])
        load_data = load_data.to_numpy().flatten()
    
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
        general_plastic_deformation_data.append(abs(depth_data[-1]-depth_data[0]))
        general_max_depth_data.append(max(depth_data))
        
    # =============================================================================
    #     Slope and slope change ratio determination
    # =============================================================================
    # In this section, the slope is calculated
    # One can adjust the way the slope is calculated here if desired    
    
        slope_data = []
        for location, depth in enumerate(depth_data_loading):
            if location == 0:
                if (depth_data_loading[location+1]-depth_data_loading[location]) == 0:
                    slope = (load_data_loading[location+1]-load_data_loading[location])/((1.000001*depth_data_loading[location+1])-depth_data_loading[location])
                    slope_data.append(slope)
                    continue
                slope = (load_data_loading[location+1]-load_data_loading[location])/(depth_data_loading[location+1]-depth_data_loading[location])
                slope_data.append(slope)
                continue
            if location == (len(load_data_loading)-1):
                if (depth_data_loading[location]-depth_data_loading[location-1]) == 0:
                    slope = (load_data_loading[location]-load_data_loading[location-1])/((1.000001*depth_data_loading[location])-depth_data_loading[location-1])
                    slope_data.append(slope)
                    continue
                slope = (load_data_loading[location]-load_data_loading[location-1])/(depth_data_loading[location]-depth_data_loading[location-1])
                slope_data.append(slope)
                continue
            if depth_data_loading[location]-depth_data_loading[location-1] == 0 or depth_data_loading[location+1]-depth_data_loading[location] == 0:
                slope_before = (load_data_loading[location]-load_data_loading[location-1])/((1.000001*depth_data_loading[location])-depth_data_loading[location-1])
                slope_after = (load_data_loading[location+1]-load_data_loading[location])/((1.000001*depth_data_loading[location+1])-depth_data_loading[location])
                slope = (slope_before+slope_after)/2
                slope_data.append(slope)
                continue
            slope_before = (load_data_loading[location]-load_data_loading[location-1])/(depth_data_loading[location]-depth_data_loading[location-1])
            slope_after = (load_data_loading[location+1]-load_data_loading[location])/(depth_data_loading[location+1]-depth_data_loading[location])
            slope = (slope_before+slope_after)/2
            slope_data.append(slope)
            
    # =============================================================================
    #     Popin indices determination
    # =============================================================================
    # This section, the pop-in start is determined with the parameters of 0.4 and 0.125 in line 131
    # If desired, these can be adjusted
    
        popin_indices = []
        popin_start_indices = []
        popin_end_indices = []
        for location, slope in enumerate(slope_data):
            if location == 0:
                continue
            if slope < 0.4*(np.median(slope_data)) and location >= int(0.125*len(slope_data)):
                popin_indices.append(location-1)
                popin_start_indices.append(location-1)
        for i in popin_start_indices:
            counter = 0
            for j in range(max_popin_length):
                counter += 1
                i += 1
                if i == len(depth_data_loading)-1:
                    break
                if slope_data[i] < 0.4*np.median(slope_data):
                    popin_indices.append(i)
                    continue
                if counter == 1:
                    popin_indices.append(i)
                    break
                break
            
    # =============================================================================
    #     Delete possible duplicate values
    # =============================================================================
    # Possible duplicate values are deleted 
    
        popin_indices = sorted(popin_indices)
        non_duplicates = []
        for i in popin_indices:
            if i not in non_duplicates:
                non_duplicates.append(i)
        popin_indices = sorted(non_duplicates)
        
        non_duplicates = []
        for i in popin_start_indices:
            if i not in non_duplicates:
                non_duplicates.append(i)
        popin_start_indices = sorted(non_duplicates)
        
    # =============================================================================
    #     Delete bug popin(s) at peak load
    # =============================================================================
    # This section deletes pop-ins at the prescribed maximum load as those "pop-ins" are likely not pop-ins
    
        indices_to_remove = []
        for i in popin_indices:
            if load_data_loading[i] >= (0.97*peak_load):
                indices_to_remove.append(i)
        for i in indices_to_remove:
            popin_indices.remove(i)
            
    # =============================================================================
    #     Clustering obtained indices and determining the number of popins
    # =============================================================================
    # This section clusters the consecutive pop-in indices to lists of indices which represent pop-ins
    
        diffs = np.diff(popin_indices) != 1 
        indices = np.nonzero(diffs)[0] + 1
        popins = np.split(popin_indices, indices)
        popins2 = []
        for i in popins:
            popins2.append(list(i))
        popins = popins2
    
    # =============================================================================
    #     Check if there are popins at all
    # =============================================================================
    # If there are no pop-ins found at all in a load-depth curve, an exception is raised and the file is skipped    
    
        if len(popin_indices) == 0:
            print(len(popin_indices))
            print("No pop-ins were detected")
            general_cumulative_popin_length_data.append(0)
            continue    
            
    # =============================================================================
    #     Popin length determination
    # =============================================================================
    # This section determines the length of the found pop-ins 
    
        popin_start_indices = []
        popin_end_indices = []
        popin_length_data = []
        popin_end_load_data = []
        popin_end_depth_data = []
        for i in popins:
            l1 = depth_data_loading[i[-1]] - depth_data_loading[i[0]]            
            if (depth_data_loading[i[-1]] - depth_data_loading[i[-2]]) == 0:
                a1 = (load_data_loading[i[-1]] - load_data_loading[i[-2]])/((1.000001*depth_data_loading[i[-1]]) - depth_data_loading[i[-2]])
            else:
                a1 = (load_data_loading[i[-1]] - load_data_loading[i[-2]])/(depth_data_loading[i[-1]] - depth_data_loading[i[-2]])                
            b1 = load_data_loading[i[-1]] - (a1*depth_data_loading[i[-1]])         
            if (depth_data_loading[(i[-1])+2] - depth_data_loading[(i[-1])+1]) == 0:
                a2 = (load_data_loading[(i[-1])+2] - load_data_loading[(i[-1])+1])/((1.000001*depth_data_loading[(i[-1])+2]) - depth_data_loading[(i[-1])+1])
            else:
                a2 = (load_data_loading[(i[-1])+2] - load_data_loading[(i[-1])+1])/(depth_data_loading[(i[-1])+2] - depth_data_loading[(i[-1])+1])
            b2 = load_data_loading[(i[-1])+1] - (a2*depth_data_loading[(i[-1])+1])        
            l2 = ((b2-b1)/(a1-a2)) - depth_data_loading[i[-1]]
            if l2 > 0:
                length = l1+l2
                popin_end_load_data.append((a1*((b2-b1)/(a1-a2)))+b1)
                popin_end_depth_data.append((b2-b1)/(a1-a2))
            else:
                length = l1
                popin_end_load_data.append(load_data_loading[i[-1]])
                popin_end_depth_data.append(depth_data_loading[i[-1]])
            popin_length_data.append(length)
            general_popin_length_data.append(depth_data_loading[i[-1]] - depth_data_loading[i[0]])
            popin_start_indices.append(int(i[0]))
            popin_end_indices.append(int(i[-1]))
        cumulative_popin_length = sum(popin_length_data)
        cumulative_popin_length_data.append(cumulative_popin_length)
        general_cumulative_popin_length_data.append(cumulative_popin_length)
        
    # =============================================================================
    #     Plotting load-depth curve and popins
    # =============================================================================
    # This section plots the load-depth curves, with pop-ins indicated
    
        plt.plot(depth_data_loading, load_data_loading, c = "b", lw = 1.5, alpha = 0.4)
        plt.scatter(depth_data_loading[popin_indices], load_data_loading[popin_indices], c = "r", alpha = 0.2, s = 3)
        for i in popins:
            popin_depth = []
            popin_load = []
            popin_counter += 1
            for j in i:
                popin_depth.append(depth_data_loading[j])
                popin_load.append(load_data_loading[j])
            plt.plot(popin_depth, popin_load, c = "r", alpha = 0.5, lw = 2)
        
    # =============================================================================
    #     Exporting data
    # =============================================================================
    # In the following section, the pop-in data is extracted to an .xlsx-file
    # If desired, one can add more lists to the table in line 283
    
        popin_start_load_data = []
        popin_start_depth_data = []
        popin_stress_data = []
        popin_strain_data = []
        popin_contact_radius_data = []
        
        for i in popins:
            popin_start_load_data.append(load_data_loading[i[0]])
            general_popin_load_data.append(load_data_loading[i[0]])
            general_popin_depth_data.append(depth_data_loading[i[0]])
            popin_start_depth_data.append(depth_data_loading[i[0]])
            a = math.sqrt(Reff*depth_data_loading[i[0]])
            popin_stress_data.append(load_data_loading[i[0]]/(math.pi*pow(a,2)))
            popin_strain_data.append(depth_data_loading[i[0]]/(2.4*a))
            general_popin_stress_data.append(load_data_loading[i[0]]/(math.pi*pow(a,2)))
            general_popin_strain_data.append(depth_data_loading[i[0]]/(2.4*a))
            popin_contact_radius_data.append(a)
            general_popin_contact_radius_data.append(a)
  
        table = {
            "Load start pop-in": popin_start_load_data,
            "Load end pop-in": popin_end_load_data,
            "Depth start pop-in (μm)": popin_start_depth_data,
            "Depth end popin (μm)": popin_end_depth_data,
            "Pop-in length (μm)": popin_length_data,
            "Pop-in stress (GPa)": popin_stress_data,
            "Pop-in strain (ε)": popin_strain_data
        }
        output_table = pd.DataFrame(table)
        path = f"{output_path}\{name_output_excel}.xlsx"
        
        if sheet_counter == 1:
            with pd.ExcelWriter(f"{name_output_excel}.xlsx") as writer:
                output_table.to_excel(writer, sheet_name = f"Popin data file {sheet_counter}")
                output_table.to_excel(path, sheet_name = f"Popin data file {sheet_counter}", index = False)
        if sheet_counter >= 2:
            with pd.ExcelWriter(path, mode = "a", engine="openpyxl") as writer:
                output_table.to_excel(writer, sheet_name= f"Popin data file {sheet_counter}", index = False)
        workbook = load_workbook(path)
        worksheet = workbook[f"Popin data file {sheet_counter}"]
        for col in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']:
            worksheet.column_dimensions[col].width = 20  
        workbook.save(path)
        sheet_counter += 1

    # =============================================================================
    #     Generation of plots
    # =============================================================================
    # In this section, plots and histrograms containing data about the found pop-ins are created
    
    plt.plot(0,0, label = "Load-depth curve", c = "b", lw = 1.5)
    plt.plot(0,0, label = "Pop-in", c = "r", lw = 1.5)
    plt.legend(loc = "upper left", fontsize = 30)
    plt.xlabel("Indentation depth (μm)", fontsize= 25)
    plt.ylabel("Load (mN)", fontsize= 25)
    plt.xticks(fontsize=25)
    plt.yticks(fontsize=25)
    plt.grid()
    
    plt.figure(figsize = (20, 12))
    plt.scatter(general_popin_load_data, general_popin_length_data)
    plt.xlabel("Load at the start of the pop-in (mN)", fontsize=25)
    plt.ylabel("Length of the pop-in (μm)", fontsize=25)
    plt.xticks(fontsize=25)
    plt.yticks(fontsize=25)
    
    plt.figure(figsize = (20, 12))
    plt.scatter(general_popin_depth_data, general_popin_length_data)
    plt.xlabel("Indentation depth at the start of the pop-in", fontsize= 25)
    plt.ylabel("Length of the pop-in (μm)", fontsize= 25)
    plt.xticks(fontsize=25)
    plt.yticks(fontsize=25)
    
    plt.figure(figsize = (20, 12))
    plt.scatter(general_plastic_deformation_data, general_cumulative_popin_length_data)
    plt.xlabel("Plastic indentation depth (μm)", fontsize= 25)
    plt.ylabel("Cumulative pop-in length (μm)", fontsize= 25)
    plt.xticks(fontsize=25)
    plt.yticks(fontsize=25)
    
    plt.figure(figsize = (20, 12))
    plt.scatter(general_max_depth_data, general_cumulative_popin_length_data)
    plt.xlabel("Maximum indentation depth (μm)", fontsize= 25)
    plt.ylabel("Cumulative pop-in depth (μm)", fontsize= 25)
    plt.xticks(fontsize=25)
    plt.yticks(fontsize=25)
    
    plt.figure(figsize = (15, 9))
    plt.hist(general_cumulative_popin_length_data, color = "blue", edgecolor = "black")
    plt.xlabel("Cumulative pop-in depth (μm)", fontsize= 25)
    plt.ylabel("Frequency", fontsize= 25)
    plt.xticks(fontsize=25)
    plt.yticks(fontsize=25)
    
    plt.figure(figsize = (20, 12))
    plt.scatter(general_popin_stress_data, general_popin_length_data)
    plt.xlabel("Stress at the start of the pop-in (GPa)", fontsize= 25)
    plt.ylabel("Pop-in length (μm)", fontsize= 25)
    plt.xticks(fontsize=25)
    plt.yticks(fontsize=25)
    
    
    plt.figure(figsize = (15, 9))
    plt.hist(general_popin_length_data, color = "blue", edgecolor = "black")
    plt.xlabel("Length of the pop-in (μm)", fontsize= 25)
    plt.ylabel("Frequency", fontsize= 25)
    plt.xticks(fontsize=25)
    plt.yticks(fontsize=25)
    
    plt.figure(figsize = (15, 9))
    plt.hist(general_popin_load_data, color = "blue", edgecolor = "black")
    plt.xlabel("Load at the start of a pop-in (mN)", fontsize= 25)
    plt.ylabel("Frequency", fontsize= 25)
    plt.xticks(fontsize=25)
    plt.yticks(fontsize=25)
    
    plt.figure(figsize = (15, 9))
    plt.hist(general_popin_depth_data, color = "blue", edgecolor = "black")
    plt.xlabel("Indentation depth at the start of a pop-in (μm)", fontsize= 25)
    plt.ylabel("Frequency", fontsize= 25)
    plt.xticks(fontsize=25)
    plt.yticks(fontsize=25)
    
    plt.figure(figsize = (15, 9))
    plt.hist(general_popin_stress_data, color = "blue", edgecolor = "black")
    plt.xlabel("Stress at the start of a pop-in (GPa)", fontsize= 25)
    plt.ylabel("Frequency", fontsize= 25)
    plt.xticks(fontsize=25)
    plt.yticks(fontsize=25)
    
    plt.figure(figsize = (15, 9))
    plt.hist(general_popin_strain_data, color = "blue", edgecolor = "black")
    plt.xlabel("Strain at the start of a pop-in (ε)", fontsize= 25)
    plt.ylabel("Frequency", fontsize= 25)
    plt.xticks(fontsize=25)
    plt.yticks(fontsize=25)
    print("Tadaa!")
    
    return

# =============================================================================
#     An example how to run Popeye
# =============================================================================
# list_with_input_files = [r"C:\Users\Documents\Research Nanoindentation Research\input_file1.xlsx,
#                          r"C:\Users\Documents\Research Nanoindentation Research\input_file2.xlsx,
#                          r"C:\Users\Documents\Research Nanoindentation Research\input_file3.xlsx
# ]    
#
# popeye(input_files = list_with_input_files,
#       name_output_excel= "Popin_data",
#       max_popin_length = 10,
#       output_path = r"C:\Users\Documents\Research Nanoindentation Research",
#       peak_load = 25,
#       Reff = 2)
# Note: peak_load is in mN and Reff in μm


