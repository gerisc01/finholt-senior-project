<?PHP
class ODT2XHTML
	{
	public function oo_unzip($file, $path = false)
		{
		IF(!function_exists('zip_open'))
			{
			throw new Exception('NO ZIP FUNCTIONS DETECTED. Do you have the PECL ZIP extensions loaded?');
			}
		IF(!is_file($file))
			{
			throw new Exception('Can\'t find file: '.$file);
			}
		IF($zip = zip_open($file))
			{
			while ($zip_entry = zip_read($zip))
				{
				$filename = zip_entry_name($zip_entry);
				IF(zip_entry_name($zip_entry) == 'content.xml' and zip_entry_open($zip, $zip_entry, "r"))
					{
					$content = zip_entry_read($zip_entry, zip_entry_filesize($zip_entry));
					zip_entry_close($zip_entry);
					}
				IF(ereg('Pictures/', $filename) and !ereg('Object', $filename)  and zip_entry_open($zip, $zip_entry, "r"))
					{
					$img[$filename] = zip_entry_read($zip_entry, zip_entry_filesize($zip_entry));
					zip_entry_close($zip_entry);
					}
				}
			IF(isset($content))
				{
				IF(is_array($img))
					{
					IF(!is_dir($path.'Pictures'))
						{
						mkdir($path.'Pictures');
						}
					foreach($img as $key => $val)
						{
						file_put_contents($path.$key, $val);
						}
					}
				return $content;
				}
			}
		}
	public function oo_convert($xml)
		{
		$xls = new DOMDocument;
		$xls->load('applications/SeniorProject/static/php/rfi_template.xsl');
		$xslt = new XSLTProcessor;
		$xslt->importStylesheet($xls);
		
		$x = preg_replace('#<draw:image xlink:href="Pictures/([a-z .A-Z_0-9]*)" (.*?)/>#es', "ODT2XHTML::makeImage('\\1')", $xml);
		
		$xml = new DOMDocument;
		$xml->loadXML($x);
		return html_entity_decode($xslt->transformToXML($xml));
		}
	public function makeImage($img)
		{
		return '&lt;img src="Pictures/'.$img.'" border="0" /&gt;';
		}
	}
?>
