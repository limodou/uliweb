from sqlalchemy import *
from sqlalchemy.schema import CreateTable
from sqlalchemy.ext.compiler import compiles

@compiles(CreateTable, "mysql")
def add_partition_scheme(element, compiler, **kw):
    table = element.element
    partition_by = table.kwargs.pop("mysql_partition_by", None)
    partitions = table.kwargs.pop("mysql_partitions", None)

    ddl = compiler.visit_create_table(element, **kw)
    ddl = ddl.rstrip()

    if partition_by:
        ddl += "\nPARTITION BY %s" % partition_by
        table.kwargs['mysql_partition_by'] = partition_by
    if partitions:
        ddl += "\nPARTITIONS %s" % partitions
        table.kwargs['mysql_partitions'] = partitions

    return ddl

