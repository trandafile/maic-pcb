# ----------------------------------------------
# Script Recorded by Ansys Electronics Desktop Version 2024.1.0
# 12:32:05  Apr 07, 2026
# ----------------------------------------------
import ScriptEnv
ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
oDesktop.RestoreWindow()
oProject = oDesktop.SetActiveProject("Project1")
oDesign = oProject.SetActiveDesign("HFSSDesign1")
oEditor = oDesign.SetActiveEditor("3D Modeler")
oEditor.CreateBox(
	[
		"NAME:BoxParameters",
		"XPosition:="		, "-0.6mm",
		"YPosition:="		, "-0.6mm",
		"ZPosition:="		, "0mm",
		"XSize:="		, "1.2mm",
		"YSize:="		, "1.2mm",
		"ZSize:="		, "0.2mm"
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
					"NAME:DielX",
					"PropType:="		, "VariableProp",
					"UserDef:="		, True,
					"Value:="		, "4mm"
				]
			]
		]
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
					"NAME:DielY",
					"PropType:="		, "VariableProp",
					"UserDef:="		, True,
					"Value:="		, "4mm"
				]
			]
		]
	])
oEditor = oDesign.SetActiveEditor("3D Modeler")
oEditor.ChangeProperty(
	[
		"NAME:AllTabs",
		[
			"NAME:Geometry3DCmdTab",
			[
				"NAME:PropServers", 
				"Box1:CreateBox:1"
			],
			[
				"NAME:ChangedProps",
				[
					"NAME:Position",
					"X:="			, "-DielX/2",
					"Y:="			, "-DielY/2",
					"Z:="			, "0mm"
				]
			]
		]
	])
oEditor.ChangeProperty(
	[
		"NAME:AllTabs",
		[
			"NAME:Geometry3DCmdTab",
			[
				"NAME:PropServers", 
				"Box1:CreateBox:1"
			],
			[
				"NAME:ChangedProps",
				[
					"NAME:XSize",
					"Value:="		, "DielX"
				]
			]
		]
	])
oEditor.ChangeProperty(
	[
		"NAME:AllTabs",
		[
			"NAME:Geometry3DCmdTab",
			[
				"NAME:PropServers", 
				"Box1:CreateBox:1"
			],
			[
				"NAME:ChangedProps",
				[
					"NAME:YSize",
					"Value:="		, "DielY"
				]
			]
		]
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
					"NAME:D1_low",
					"PropType:="		, "VariableProp",
					"UserDef:="		, True,
					"Value:="		, "0mm"
				]
			]
		]
	])
oEditor.ChangeProperty(
	[
		"NAME:AllTabs",
		[
			"NAME:Geometry3DCmdTab",
			[
				"NAME:PropServers", 
				"Box1:CreateBox:1"
			],
			[
				"NAME:ChangedProps",
				[
					"NAME:Position",
					"X:="			, "-DielX/2",
					"Y:="			, "-DielY/2",
					"Z:="			, "D1_low"
				]
			]
		]
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
					"NAME:D1_high",
					"PropType:="		, "VariableProp",
					"UserDef:="		, True,
					"Value:="		, "0.4mm"
				]
			]
		]
	])
oEditor.ChangeProperty(
	[
		"NAME:AllTabs",
		[
			"NAME:Geometry3DCmdTab",
			[
				"NAME:PropServers", 
				"Box1:CreateBox:1"
			],
			[
				"NAME:ChangedProps",
				[
					"NAME:ZSize",
					"Value:="		, "D1_high"
				]
			]
		]
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
					"NAME:StackUp",
					"PropType:="		, "SeparatorProp",
					"UserDef:="		, True,
					"Value:="		, ""
				],
				[
					"NAME:L1_low",
					"PropType:="		, "VariableProp",
					"UserDef:="		, True,
					"Value:="		, "D1_high"
				],
				[
					"NAME:L1_h",
					"PropType:="		, "VariableProp",
					"UserDef:="		, True,
					"Value:="		, "18um"
				],
				[
					"NAME:L1_high",
					"PropType:="		, "VariableProp",
					"UserDef:="		, True,
					"Value:="		, "L1_low+L1_h"
				],
				[
					"NAME:D1_h",
					"PropType:="		, "VariableProp",
					"UserDef:="		, True,
					"Value:="		, "0.4mm"
				]
			],
			[
				"NAME:ChangedProps",
				[
					"NAME:StackUp",
					"NewRowPosition:="	, 0
				],
				[
					"NAME:D1_high",
					"Value:="		, "D1_low+D1_h"
				],
				[
					"NAME:D1_h",
					"NewRowPosition:="	, 5
				]
			]
		]
	])
