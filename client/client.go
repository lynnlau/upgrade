// client.go
package main

import (
	"flag"
	"fmt"
	"log"
	"net"
	//	"strconv"
	"sync"
	"time"
)

type term struct {
	C    int
	apdu *[]byte
	conn net.Conn
}

func (t term) send(apdu []byte) {
	c, _ := t.conn.Write(apdu)
	fmt.Println(c)
}
func login(self term) {
	apdu := []byte{0x01, 0x00, 0x00, 0x00, 0xb4, 0x07, 0xe2, 0x08, 0x0f, 0x03, 0x11, 0x25, 0x1d, 0x01, 0x82}
	self.C = 0x81
	self.apdu = &apdu
	fmt.Println("连接成功！\n")
	self.send(*self.apdu)
	self.C = 0x88
}
func Client(No int) {
	self := term{}
	conn, err := net.Dial("tcp", "localhost:8888")
	checkError(err)
	self.conn = conn
	login(self)
	//	buffer := make([]byte, 2048)
	//Rx := make([]byte, 2048)

}

//检查错误
func checkError(err error) {
	if err != nil {
		log.Fatal("an error!", err.Error())
	}
}

//主函数
func main() {
	var goCount *int
	var waitgroup sync.WaitGroup
	goCount = flag.Int("goCount", 10, "goroutine number")
	//解析输入的参数
	flag.Parse()
	fmt.Println("go count = ", *goCount)
	//get current time
	tInsert := time.Now()
	fmt.Println("tStart time: ", tInsert)
	for i := 0; i < *goCount; i++ {
		fmt.Println("goroutine number: ", i)
		waitgroup.Add(1) //每创建一个goroutine，就把任务队列中任务的数量+1
		go Client(i)
	}

	waitgroup.Wait() //.Wait()这里会发生阻塞，直到队列中所有的任务结束就会解除阻塞
	//获取时间差
	elapsed := time.Since(tInsert)
	fmt.Println("Insert elapsed: ", elapsed)
	fmt.Println("/n")
}
