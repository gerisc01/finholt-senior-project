<?php
//echo shell_exec('rm result.odt');
//echo system('python get_db.py');
require('odt2xhtml.php');

$class = new ODT2XHTML;
$xhtml = $class->oo_convert($class->oo_unzip('/home/seniorproj/Documents/finholt-senior-project/web2py/applications/SeniorProject/static/php/result.odt'));

echo $xhtml;
//$new_file = 'test.html';
//$handle = fopen($new_file, 'w');
//fwrite($handle, $xhtml);

?>