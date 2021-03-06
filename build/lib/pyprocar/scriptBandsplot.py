  
from utilsprocar import UtilsProcar
from procarparser import ProcarParser
from procarselect import ProcarSelect
from procarplot import ProcarPlot
import numpy as np
import matplotlib.pyplot as plt
import re



  
def bandsplot(file,mode='scatter',abinit_output=None,spin='0',atoms=None,orbitals=None,fermi=None,elimit=None,mask=None,markersize=10,cmap='hot_r',vmax=None,vmin=None,grid=True,marker='o',permissive=False,human=False,savefig=None,kticks=None,knames=None,title=None,outcar=None):
  #First handling the options, to get feedback to the user and check
  #that the input makes sense.
  #It is quite long
  if atoms is None:
    atoms = [-1]
    if human is True:
      print "WARNING: `--human` option given without atoms list!"
      print "--human will be set to False (ignored)\n "
      human = False
  if orbitals is None:
    orbitals = [-1]
    

  print "Script initiated"
  print "input file    : ", file
  print "Mode          : ", mode
  
  print "spin comp.    : ", spin
  print "atoms list.   : ", atoms
  print "orbs. list.   : ", orbitals

  if fermi is None and outcar is None and abinit_output is None:
    print "WARNING: Fermi Energy not set! "
    print "You should use '-f' or '--outcar'\n Are you using Abinit Procar?\n"
    print "The zero of energy is arbitrary\n"
    fermi = 0


###################reading abinit output (added by uthpala) ##########################

  if abinit_output:
  	print "Abinit output used"

  #reading abinit output file
  	rf = open(abinit_output,'r')
  	data = rf.read()
  	rf.close()

  	fermi = float(re.findall('Fermi\w*.\(\w*.HOMO\)\s*\w*\s*\(\w*\)\s*\=\s*([0-9.+-]*)',data)[0])


####################################################################  

 
  print "Fermi Ener.   : ", fermi
  print "Energy range  : ", elimit

  if mask is not None:
    print "masking thres.: ", mask
    
  print "Colormap      : ", cmap
  print "MarkerSize    : ", markersize
    
  print "Permissive    : ", permissive
  if permissive:
    print "INFO: Permissive flag is on! Be careful"
  print "vmax          : ", vmax
  print "vmin          : ", vmin
  print "grid enabled  : ", grid 
  if human is not None:
    print "human         : ", human
  print "Savefig       : ", savefig
  print "kticks        : ", kticks
  print "knames        : ", knames
  print "title         : ", title

  print "outcar        : ", outcar

  #If ticks and names are given we should use them#
  if kticks is not None and knames is not None:
    ticks = zip(kticks,knames)
  elif kticks is not None:
    ticks = zip(kticks,kticks)
  else:
    ticks = None
  
  #The spin argument should be a number (index of an array), or
  #'st'. In the last case it will be handled separately (later)
  spin = {'0':0, '1':1, '2':2, '3':3, 'st':'st'}[spin]


  #The second part of this function is parse/select/use the data in
  #OUTCAR (if given) and PROCAR

  #first parse the outcar if given, to get Efermi and Reciprocal lattice
  recLat = None 
  if outcar:
    outcarparser = UtilsProcar()
    if fermi is None:
      fermi = outcarparser.FermiOutcar(outcar)
      #if quiet is False:
      print "INFO: Fermi energy found in outcar file = " + str(fermi)
    recLat = outcarparser.RecLatOutcar(outcar)

  # parsing the PROCAR file
  procarFile = ProcarParser()
  procarFile.readFile(file, permissive, recLat)

  # processing the data, getting an instance of the class that reduces the data
  data = ProcarSelect(procarFile, deepCopy=True)
  
  #handling the spin, `spin='st'` is not straightforward, needs
  #to calculate the k vector and its normal. Other `spin` values
  #are trivial.
  if spin is 'st':
    #two `ProcarSelect` instances, to store temporal values: spin_x, spin_y
    dataX = ProcarSelect(procarFile, deepCopy=True)
    dataX.selectIspin([1])
    dataX.selectAtoms(atoms, fortran=human)
    dataX.selectOrbital(orbitals)  
    dataY = ProcarSelect(procarFile, deepCopy=True)
    dataY.selectIspin([2])
    dataY.selectAtoms(atoms, fortran=human)
    dataY.selectOrbital(orbitals)
    #getting the signed angle of each K-vector
    angle = np.arctan2(dataX.kpoints[:,1], (dataX.kpoints[:,0]+0.000000001))
    sin = np.sin(angle)
    cos = np.cos(angle)
    sin.shape = (sin.shape[0],1)
    cos.shape = (cos.shape[0],1)
    ##print sin, cos
    #storing the spin projection into the original array
    data.spd = -sin*dataX.spd + cos*dataY.spd
  else:
    data.selectIspin([spin])
    data.selectAtoms(atoms, fortran=human)
    data.selectOrbital(orbitals)

  # Plotting the data
  data.bands = (data.bands.transpose() - np.array(fermi)).transpose()
  plot = ProcarPlot(data.bands, data.spd, data.kpoints)

  ###### start of mode dependent options #########

  if mode == "scatter":
    plot.scatterPlot(mask=mask, size=markersize,
                     cmap=cmap, vmin=vmin,
                     vmax=vmax, marker=marker, ticks=ticks)

    plt.ylabel(r"Energy [eV]")
    if elimit is not None:
      plt.ylim(elimit)

  elif mode == "plain":
    plot.plotBands(markersize, marker=marker, ticks=ticks)
    plt.ylabel(r"Energy [eV]")
    if elimit:
      plt.ylim(elimit)
      
  elif mode == "parametric":
    plot.parametricPlot(cmap=cmap, vmin=vmin, vmax=vmax,
                        ticks=ticks)
    plt.ylabel(r"Energy [eV]")
    if elimit is not None:
      plt.ylim(elimit)

  elif mode == "atomic":
    plot.atomicPlot(cmap=cmap, vmin=vmin, vmax=vmax)
    plt.ylabel(r"Energy [eV]")
    if elimit is not None:
      plt.ylim(elimit)
  ###### end of mode dependent options ###########

  if grid:
    plt.grid()
  
  if title:
    plt.title(title)

  if savefig:
    plt.savefig(savefig,  bbox_inches=0)
  else:
    plt.show()

  return