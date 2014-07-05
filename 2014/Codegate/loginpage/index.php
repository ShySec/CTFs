 <?php
mysql_connect("localhost","","");
mysql_select_db("");
?>

<!DOCTYPE html>
<html>
<head>
    <style type="text/css">
    body { background:silver; }
    div { background:url('bg.png');width:90%;height:150pt;text-align:left;font-size:15pt; color:black;margin:20pt;padding:10pt;border:10pt solid gray; border-radius:50pt; }
    a { color:green; }
    input[type=text] { width:150pt; font-size:15pt; }
    input[type=submit],input[type=button] { font-size:15pt; font-family:'impact'; }
    .error { color:green; font-weight:bold;font-size:20pt;text-align:center; }
    .msg { text-align:center;color:#363636;font-weight:bold;margin:0;padding:0;background:gray;border-radius:20pt;font-size:15pt; }
    </style>
    <title>Login</title>
</head>
<body>
<form method=get action="index.php">
<div>
<h1>Login</h1>
ID <input type=text name=id> PW <input type=text name=pw> <input type=submit value='Submit'> <input type=button onclick=location.href='index.phps' value='Source'>
</form>
<?php
$q=@mysql_fetch_array(mysql_query("select id,pw from mem where id='$_GET[id]'"));

if($_GET['id'] && $_GET['pw'])
{
    if(!$q['id']) exit();

    if(md5($q['id'])==md5($_GET['id']))
    {
        echo("<br>hi! ".htmlspecialchars($q['id'])."<br><br>");
        $q['pw']=trim($q['pw']);
        $_GET['pw']=trim($_GET['pw']);

        if(!$q['pw']) exit();

        if($q['pw']==md5($_GET['pw'])) {
            echo("<p class=msg>Password is ????</p>");
        }

        else {
            echo("<p class=error>Wrong pw</p>");
        }
    }

    else
    {
        echo("<p class=error>Wrong id</p>");
    }
}

?>
</div>
</body>
</html>
