# ----------------------------------------------
# Script Recorded by Ansys Electronics Desktop Version 2024.1.0
# 21:25:09  Apr 07, 2026
# ----------------------------------------------
import ScriptEnv
ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
oDesktop.RestoreWindow()
oProject = oDesktop.SetActiveProject("Project2")
oDesign = oProject.SetActiveDesign("HFSSDesign1")
oEditor = oDesign.SetActiveEditor("3D Modeler")
oEditor.CreateBox(
	[
		"NAME:BoxParameters",
		"XPosition:="		, "-0.6mm",
		"YPosition:="		, "-0.8mm",
		"ZPosition:="		, "0mm",
		"XSize:="		, "1.2mm",
		"YSize:="		, "1.4mm",
		"ZSize:="		, "0.4mm"
	], 
	[
		"NAME:Attributes",
		"Name:="		, "Box1",
		"Flags:="		, "",
		"Color:="		, "(143 175 143)",
		"Transparency:="	, 0,
		"PartCoordinateSystem:=", "Global",
		"UDMId:="		, "",
		"MaterialValue:="	, "\"vacuum\"",
		"SurfaceMaterialValue:=", "\"\"",
		"SolveInside:="		, True,
		"ShellElement:="	, False,
		"ShellElementThickness:=", "0mm",
		"ReferenceTemperature:=", "20cel",
		"IsMaterialEditable:="	, True,
		"UseMaterialAppearance:=", False,
		"IsLightweight:="	, False
	])
oDesign.ChangeProperty(
	[
		"NAME:AllTabs",
		[
			"NAME:LocalVariableTab",
			[
				"NAME:PropServers", 
				"LocalVariables"
			],
			[
				"NAME:NewProps",
				[
					"NAME:PCB_variables",
					"PropType:="		, "SeparatorProp",
					"UserDef:="		, True,
					"Value:="		, ""
				],
				[
					"NAME:D1_low",
					"PropType:="		, "VariableProp",
					"UserDef:="		, True,
					"Value:="		, "0mm"
				],
				[
					"NAME:D1_h",
					"PropType:="		, "VariableProp",
					"UserDef:="		, True,
					"Value:="		, "2mm"
				],
				[
					"NAME:D1_high",
					"PropType:="		, "VariableProp",
					"UserDef:="		, True,
					"Value:="		, "D1_low+D1_h"
				]
			]
		]
	])
