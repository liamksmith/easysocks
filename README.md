# easysocks
Code for Research/Development Purposes.

实验目标
1. 用asyncio实现一个socks5服务器。
2. 加入local端,在local和server之间实现无加密的forward。
3. 实现local和server之间的多路复用，所有local和server来回的数据都在一个socket连接上传输。
4. 用TLS在local和server之间传输数据。
5. 添加一个简单的用户身份验证功能，在server端实现用户身份验证。
