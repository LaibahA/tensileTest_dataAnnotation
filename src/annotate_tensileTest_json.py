from rdflib import Graph, Namespace, Literal
# Graph stores the RDF triples, Namespace is what lets us define the prefixes
from rdflib.namespace import RDF, XSD
# RDF is for the standard datatypes
import json

g = Graph() # Empty graph to store triples

TTO = Namespace("https://materialdigital.github.io/application-ontologies/tto/#/") # Here we are just saying that TTO is the namespace for our ontology
g.bind("tto", TTO) # Binding namespace to prefix, makes it easier to use

QUDT = Namespace("http://qudt.org/schema/qudt/")
g.bind("qudt", QUDT)

'''
Need to update namespace below
'''
EX = Namespace("http://example.org/tensile/") # This is an example, its gna be what builds the uri for our subject to annotate.
g.bind("ex", EX)

#for file in directory full of data files:
#with open("../data/FAIRtrain") as f:
with open("../data/example/sample_data.json") as f:
    data = json.load(f) # Makes the list of rows

    #Make uris
    sample_id = data["sample_id"]
    test_uri = EX[sample_id]
    test_piece_id = sample_id.split("_")[2]
    test_piece_uri = EX["testPiece_" + test_piece_id]
    machine_uri = EX[data["sample_id"][:6]]

    #Declare test, test machine, and test piece
    g.add((test_uri, RDF.type, TTO.TensileTest))
    g.add((test_piece_uri, RDF.type, TTO.TestPiece))
    g.add((machine_uri, RDF.type, TTO.TensileTestingMachine))

    #Establish relationships between tensile test to test piece and machine
    g.add((test_uri, TTO.relatesTo, test_piece_uri))
    g.add((test_uri, TTO.relatesTo, machine_uri))

    # Original width
    width_node = EX[f"width"]
    g.add((width_node, RDF.type, TTO.OriginalWidth))
    g.add((width_node, QUDT.numericValue, Literal(data["width"], datatype=XSD.float)))
    g.add((width_node, TTO.relatesTo, test_piece_uri))

    # Original thickness
    thickness_node = EX[f"thickness"]
    g.add((thickness_node, RDF.type, TTO.OriginalThickness))
    g.add((thickness_node, QUDT.numericValue, Literal(data["thickness"], datatype=XSD.float)))
    g.add((thickness_node, TTO.relatesTo, test_piece_uri))

    # Gauge length
    length_node = EX[f"length"]
    g.add((length_node, RDF.type, TTO.OriginalGaugeLength))
    g.add((length_node, QUDT.numericValue, Literal(data["length"], datatype=XSD.float)))
    g.add((length_node, TTO.relatesTo, test_piece_uri))

    # Youngs modulus / slope of the elastic part
    youngs_mod_node = EX[f"youngs_modulus"]
    g.add((youngs_mod_node, RDF.type, TTO.SlopeOfTheElasticPart))
    g.add((youngs_mod_node, QUDT.numericValue, Literal(data["extracted_properties"]["youngs_modulus"], datatype=XSD.float)))
    g.add((youngs_mod_node, TTO.relatesTo, test_piece_uri))

    # Ultimate tensile strength / upper yield strength
    ult_tensile_strength = EX[f"ultimate_tensile_strength"]
    g.add((ult_tensile_strength, RDF.type, TTO.UpperYieldStrength))
    g.add((ult_tensile_strength, QUDT.numericValue, Literal(data["extracted_properties"]["ultimate_tensile_strength"], datatype=XSD.float)))
    g.add((ult_tensile_strength, TTO.relatesTo, test_piece_uri))

    for i, point in enumerate(data["data"]):
        # Force
        force_node = EX[f"pair_{i}_force"]
        g.add((force_node, RDF.type, TTO.Force))
        g.add((force_node, QUDT.numericValue, Literal(point["N"], datatype=XSD.float)))
        g.add((force_node, TTO.relatesTo, test_piece_uri))

        # Elongation
        elong_node = EX[f"pair_{i}_elongation"]
        g.add((elong_node, RDF.type, TTO.Elongation))
        g.add((elong_node, QUDT.numericValue, Literal(point["mm"], datatype=XSD.float)))
        g.add((elong_node, TTO.relatesTo, test_piece_uri))

        # Pairing the elongation and force
        g.add((elong_node, TTO.relatesTo, force_node))


output_base = f"annotated_{sample_id}"
g.serialize(f"../output/FAIRtrain/ttl_output/{output_base}.ttl", format="turtle")
g.serialize(f"../output/FAIRtrain/jsonld_output/{output_base}.jsonld", format="json-ld")
