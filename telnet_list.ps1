Function New-TelnetClient {
    [CmdletBinding()]
    Param (
        [Parameter()]
        [string]$ComputerName = '127.0.0.1'
        ,
        [Parameter()]
        [int]$PortNo = 23
        ,
        [Parameter()]
        [System.Text.Encoding]$Encoding = [System.Text.Encoding]::ASCII
        ,
        [Parameter()]
        [int]$BufferSize = 1024
    )
    [System.Net.Sockets.TcpClient]$telnet = New-Object 'System.Net.Sockets.TcpClient'
    try {
        $telnet.PSTypeNames.Add('ClearChannel.Net.Sockets.TelnetClient')
        $telnet | Add-Member -MemberType 'NoteProperty' -Name 'Encoding' -Value ($Encoding)
        $telnet | Add-Member -MemberType 'NoteProperty' -Name 'EndOfCommand' -Value ([System.Environment]::NewLine)
        $telnet | Add-Member -MemberType 'NoteProperty' -Name 'BufferSize' -Value ($BufferSize)
        $telnet.Connect($ComputerName, $PortNo)
        $telnet | Add-Member -MemberType 'NoteProperty' -Name 'Writer'      -Value (New-Object -TypeName 'System.IO.StreamWriter' -ArgumentList ($telnet.GetStream()))
        $telnet.Writer.AutoFlush = $true
        $telnet | Add-Member -MemberType 'ScriptMethod' -Name 'SendCommand' -Value ({
            Param([string]$CommandText)
            #$this.Writer.WriteLine($CommandText + $this.EndOfCommand) #writeline should stick the line endings in place anyway, but just to be sure, added this
            $this.Writer.WriteLine($CommandText)
            (New-Object -TypeName 'PSObject' -Property @{Direction='Input'; Value=$CommandText; When=((Get-Date).ToUniversalTime())})
        })
        $telnet | Add-Member -MemberType 'ScriptMethod' -Name 'HandleIac' -Value ({
            if ($this.Available) {
                [int]$byte = $this.GetStream().ReadByte()
                [byte]$defaultResponse = 254 # for most IAC requests, we'll respond with don't
                switch ($byte) {
                    -1 { # end of stream (shouldn't happen, but handled in case)
                        Write-Warning 'Unexpected end of stream whilst processing IAC'
                        return
                    }
                    255 { # Escaped IAC character
                        Write-Debug 'IAC Escaped'
                        return $byte
                    }
                    253 { #if we get a DO, change default response to WON'T instead of DON'T
                        $defaultResponse = 252
                        # do not break; continue to next case statement
                    }
                    {(251, 252, 253, 254) -contains $_} { # Will, Won't, Do, Don't
                        $byte = $this.GetStream().ReadByte() # this is the option we need to respond to; currently we just deny all options to get a raw NVT
                        switch ($byte) {
                            -1 {
                                Write-Warning 'Unexpected end of stream whilst processing IAC'
                            }
                            # if we want to handle specific IAC codes we can add support here
                            default {
                                $this.GetStream().WriteByte(255)              # IAC
                                $this.GetStream().WriteByte($defaultResponse) # Don't/Won't
                                $this.GetStream().WriteByte($byte)            # whatever you told me
                            }
                        }
                        return
                    }
                    default {
                        Write-Warning "$byte is not a control character, but was received after an IAC character"
                    }

                }
            }
        })
        $telnet | Add-Member -MemberType 'ScriptMethod' -Name 'GetBytes'   -Value ({
            Start-Sleep -Milliseconds 500 #added to get correct output; otherwise we seem to fly past the handshake :/
            while ($this.Available -gt 0) {
                [int]$byte = $this.GetStream().ReadByte() #held as int to allow -1 status code for end of stream
                switch ($byte) {
                    -1 { # end of stream
                        return
                    }
                    255 { #IAC control character received
                        Write-Verbose 'IAC Command Received'
                        $this.HandleIac()
                        break
                    }
                    {($_ -ge 0) -and ($_ -lt 255)} { # normal data (not sure if it's worth returning the 0s... haven't seen anything to suggest that they're special though, as -1 is the eof.
                        [byte]$byte
                        Write-Debug "found $byte"
                        break
                    }
                    default {
                        throw "Received value $_ when expecting a byte (0-255)"
                    }

                }
            }
        })
        $telnet | Add-Member -MemberType 'ScriptMethod' -Name 'GetOutput'   -Value ({
            [byte[]]$bytes = $this.GetBytes()
            if (($null -ne $bytes) -and ($bytes.Length -gt 0)) {
                Write-Verbose "raw output is $(($bytes | %{"$_"}) -join ', ')"
                $this.Encoding.GetString($bytes)
            } else {
                write-verbose 'no output this time'
            }
        })
        $telnet | Add-Member -MemberType 'ScriptMethod' -Name 'ReceiveThenSendCommands' -Value ({
            Param([string[]]$Commands)
            foreach ($commandText in $commands) {
                $this.GetOutput()
                $this.SendCommand($commandText)
            }
            $this.GetOutput()
        })
        if ($telnet.Connected) {
            $telnet
        } else {
            throw 'Failed to connect'
        }
    } catch {
        Remove-TelnetClient -TelnetClient $telnet
    }
}

Function Remove-TelnetClient {
    [CmdletBinding()]
    Param (
        [Parameter(Mandatory = $true)]
        [AllowNull()]
        [PSObject]$TelnetClient
    )
    if ($null -ne $TelnetClient) {
        if ($TelnetClient.Connected) {
            $TelnetClient.GetStream().Close()
            $TelnetClient.Close()
        }
        if($TelnetClient.Dispose) {
            $TelnetClient.Dispose()
        }
    }
}


(1..255)|%  {
    $ip='100.64.0.'+$_;
    $exitcode=(ping -n 1 -w 1 $ip | Select-String 'TTL').Length;
    if($exitcode -ne 0 ){
        #Write-Output $ip;
        $telnet=New-TelnetClient  $ip;
        if ($telnet){
            
            $telnet.SendCommand('admin')|out-null;
            $output=$telnet.GetOutput();
            $telnet.SendCommand($huawei)|out-null;
            $output=$telnet.GetOutput();
            $o=$ip+$output.split()[-1];
            write-output $o;
        }


    }
}