g = Graph()  #Empty graph to store triples
TTO = Namespace("https://materialdigital.github.io/application-ontologies/tto/#/")  #TTO is the ontology namespace
g.bind("tto", TTO)  #Base

process_id = data["sample"]
width = data["Properties"]["width"]
thickness = data["Properties"]["thickness"]
gauge_length = data["Properties"]["gauge_length"]
ymVal = data["youngs_modulus"]["value"]

experimentIRI = URIRef(prefix + process_id)
g.add((experimentIRI, RDF.type, PMD.PMD_0000017)) #ExperimentIRI is an identifier
processIRI = URIRef(experimentIRI + "_process")
g.add((processIRI, RDF.type, PMD.PMD_0000974)) #ProcessIRI is a tensile testing process
g.add((experimentIRI, OBO.IAO_0000219, processIRI))  # ExperimentIRI denotes tensile testing process
testPieceIRI = URIRef(experimentIRI + "_test_piece")
g.add((testPieceIRI, RDF.type, TTO.TTO_0000055))
g.add((processIRI, PMD.PMD_0000015, testPieceIRI)) #ProcessIRI has input test piece

#Thickness quality
thicknessIRI_quality = URIRef(experimentIRI + "_thickness_quality")
g.add((thicknessIRI_quality, RDF.type, TTO.OriginalThickness))  # is an OriginalThickness
g.add((processIRI, PMD.PMD_0000016, thicknessIRI_quality))  # has output quality thickness
g.add((testPieceIRI, OBO.BFO_0000196, thicknessIRI_quality))  # bears the quality of thickness
#Thickness specification
thicknessIRI_scalar_value = URIRef(experimentIRI + "_thickness_scalar_value_specification")
g.add((thicknessIRI_scalar_value, RDF.type, PMD.PMD_0000022))  # is a scalar value specification
g.add((thicknessIRI_scalar_value, PMD.PMD_0000006, Literal(thickness, datatype=XSD.float))) # has value literal
g.add((thicknessIRI_scalar_value, PMD.PMD_0060001, thicknessIRI_quality)) # specifies value of quality thickness
g.add((thicknessIRI_scalar_value, OBO.IAO_0000136, testPieceIRI))  # is about test piece

with open(csv_filename, mode="w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Force(N)", "Elongation(mm)"])  # header

datasetIRI = URIRef(experimentIRI + "_dataset")
g.add((processIRI, PMD.PMD_0000016, datasetIRI)) #processIRI has output dataset datasetIRI
g.add((datasetIRI, RDF.type, CSVW.Table)) # is a table
