from rdflib import Graph, Namespace, Literal
# Graph stores the RDF triples, Namespace is what lets us define the prefixes, Literal is in case we have nums/strings
from rdflib.namespace import RDF, XSD
# RDF is for the standard datatypes, XSD is so the values we write serialize how we want. see usage for gauge length example
import json

g = Graph() # Empty graph to store triples

TTO = Namespace("https://materialdigital.github.io/application-ontologies/tto/#/") # Here we are just saying that TTO is the namespace for our ontology
g.bind("tto", TTO) # Binding namespace to prefix, makes it easier to use

EX = Namespace("http://example.org/tensile/") # This is an example, its gna be what builds the uri for our subject to annotate
g.bind("ex", EX)

with open("../../data/example/example_5column.json") as f:
    reader = json.load(f) # Makes the list of rows

for row in reader:
    test_uri = EX[row["TestID"]]  # test_uri is the uri for the test, eg. http://example.org/tensile/T1
    test_piece_uri = EX[row["TestPiece"]] # http://example.org/tensile/machineA
    machine_uri = EX[row["Machine"]] # http://example.org/tensile/SpecimenA

    g.add((test_uri, RDF.type, TTO.TensileTest)) # This says: test_uri (eg, T1 is the subject), is a (RDF.type is the predicate), tensileTest (object)
    g.add((test_uri, TTO.hasTestPiece, test_piece_uri)) # This says : test_uri (subject), has test piece (predicate), specific test piece (eg specimenA, object)
    g.add((test_uri, TTO.hasTestingMachine, machine_uri)) # This says : test_uri (subject), has testing machine (predicate), machine_uri (eg machineA, object)
    g.add((test_uri, TTO.hasGaugeLength, Literal((row["GaugeLength"]), datatype=XSD.float))) # This says: test_uri (subject), has gauge length (predicate), specified gauge length (object)
    g.add((test_piece_uri, TTO.hasOriginalThickness, Literal((row["OriginalThickness"]), datatype=XSD.float))) # This says : test_uri (subject) has original thickness (predicate), specified thickness (object)
    # Notice how this applies the og thickness to the test piece not the test id

g.serialize("../output/example/5column/json_input_turtle_output.ttl", format="turtle")
g.serialize("../output/example/5column/json_input_jsonld_output.jsonld", format="json-ld")
