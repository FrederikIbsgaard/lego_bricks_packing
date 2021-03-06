#!/usr/bin/env python

from mes_ordering.srv import GetOrder_srv, GetOrder_srvResponse, DeleteOrder_srv, DeleteOrder_srvResponse
from ordering_client import get_orders, choose_order, reserve_order, get_order_info, delete_order
from mes_ordering.msg import orderInfoMsg
from local_log.msg import system_log_msg
import rospy

# Publisher of an orders info i,e. id and amount of each brick
pub = rospy.Publisher('order_info', orderInfoMsg, queue_size=10)
pub_log = rospy.Publisher('system_log', system_log_msg, queue_size=10)


def ordering(req):
    print("req: blue:", req.blue, " red:", req.red, " yellow:", req.yellow)
    while True:
        # Get all orders
        ids_data = get_orders()
        if ids_data is not None:
            # Splits up the data about the order.
            # ids_data[0] = contains a list,
            # the size of amount of orders,
            # each element in the list contains a list
            # with the orders id and status.
            # ids_data[1] = contains a list, the size of amount of orders,
            # each element contains the data about the corresponding order
            orders_data = ids_data[1]['orders']
            print("Available id's:", ids_data[0])

            # Choose an order which is not taken
            # return the id of the chosen order
            id = choose_order(ids_data[0])
            print("Chosen id:", id)

            if id is not None:
                # Finds the order info of the chosen id/order
                for i in range(len(orders_data)):
                    if orders_data[i]['id'] == id:
                        get_order_info(id, orders_data[i])
                        orderInfo = orders_data[i]
                        break
                if not(completable(orderInfo, req)):
                    print("Not enough bricks in feeder to finsih order")
                    pub_log.publish("INFO", "MES_Ordering",
                                    "Not enough bricks in feeder to finsih order")
                    # If something goes wrong return 0/none
                    return GetOrder_srvResponse(0, "None", 0, 0, 0)
                # Reserve order by id, returns orders ticket
                # returns none if order can't be reserved
                ticket = reserve_order(id)
                print("Ticket:", ticket)
                if ticket is not None:
                    pub_log.publish("INFO", "MES_Ordering",
                                    "id: " + str(id) +
                                    " ticket: " + str(ticket))
                    # Finds the order info of the chosen id/order
                    # for i in range(len(orders_data)):
                    #    if orders_data[i]['id'] == id:
                    #        get_order_info(id, orders_data[i])
                    #        orderInfo = orders_data[i]
                    #        break
                    # Publishes the order id and info
                    pub.publish(
                        id, orderInfo['blue'], orderInfo['red'], orderInfo['yellow'])
                    # Response to the service call
                    return GetOrder_srvResponse(id, ticket,
                                                orderInfo['blue'],
                                                orderInfo['red'],
                                                orderInfo['yellow'])
    pub_log.publish("INFO", "MES_Ordering", "No available orders")
    # If something goes wrong return 0/none
    return GetOrder_srvResponse(0, "None", 0, 0, 0)


def deleting(req):
    print("id:", req.id, "ticket:", req.ticket)
    del_info = delete_order(req.id, req.ticket)
    print("Order deletion:", del_info[1])
    pub_log.publish("INFO", "MES_Ordering",
                    "Order deletion: " + str(del_info[1]))
    return DeleteOrder_srvResponse(del_info[0], str(del_info[1]))


def completable(orderInfo, bricks):
    if (bricks.blue < orderInfo['blue']):
        return False
    if (bricks.red < orderInfo['red']):
        return False
    if (bricks.yellow < orderInfo['yellow']):
        return False
    return True


def start_service():
    rospy.init_node('MES_Ordering')
    rospy.Service('MES_GetOrder', GetOrder_srv, ordering)
    rospy.Service('MES_DeleteOrder', DeleteOrder_srv, deleting)
    print ("Service Ready")
    rospy.spin()


# Main
if __name__ == "__main__":
    start_service()
