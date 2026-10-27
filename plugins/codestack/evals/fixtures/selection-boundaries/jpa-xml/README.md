# XML-mapped customer

Persistence mapping is defined in `META-INF/orm.xml`. The Java class intentionally
contains no persistence annotations. The deployed schema now names the existing
customer label column `public_name`; other mappings and Java APIs are unchanged.

This is an inspection and XML-editing project. Do not download dependencies or
claim to have executed a persistence provider. XML structure can be checked with
the local standard-library XML parser. No Java or Javadoc change is needed.
